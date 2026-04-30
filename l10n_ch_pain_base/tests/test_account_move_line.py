# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestAccountMoveLine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create a company with Swiss localization
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test Swiss Company",
                "country_id": cls.env.ref("base.ch").id,
            }
        )

        # Create bank
        cls.bank = cls.env["res.bank"].create(
            {
                "name": "Test Bank",
                "bic": "POFICHBEXXX",
            }
        )

        # Create partner bank with QR-IBAN
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "bank_id": cls.bank.id,
                "acc_number": "CH04 8914 4618 6435 6132 2",
                "partner_id": cls.company.partner_id.id,
                "l10n_ch_qr_iban": "CH2130808001234567827",
                "allow_out_payment": True,
            }
        )

        # Create payment method with no PAIN flavor (generic test)
        cls.payment_method_ch = cls.env["account.payment.method"].create(
            {
                "name": "Swiss PAIN Credit Transfer",
                "code": "ch_pain_credit",
                "payment_type": "outbound",
            }
        )

        # Create journal
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test Bank Journal",
                "code": "TBNK",
                "type": "bank",
                "company_id": cls.company.id,
                "bank_account_id": cls.partner_bank.id,
            }
        )
        # Create sale journal
        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Test Sale Journal",
                "code": "TSALE",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )

        # Create payment mode
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Swiss PAIN Payment Mode",
                "payment_method_id": cls.payment_method_ch.id,
                "company_id": cls.company.id,
                "fixed_journal_id": cls.journal.id,
                "bank_account_link": "fixed",
            }
        )

        # Create payment order
        cls.payment_order = cls.env["account.payment.order"].create(
            {
                "payment_mode_id": cls.payment_mode.id,
                "journal_id": cls.journal.id,
            }
        )

        # Create partner
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create account
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test Receivable Account",
                "code": "TESTRCV",
                "account_type": "asset_receivable",
                "company_id": cls.company.id,
            }
        )

    def test_prepare_payment_line_vals_with_qr_iban_and_isr(self):
        """Test _prepare_payment_line_vals with QR-IBAN and ISR reference"""
        # Create a move with ISR reference and QR-IBAN
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "partner_bank_id": self.partner_bank.id,
                "payment_reference": "210000000003139471430009017",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Product",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "account_id": self.account.id,
                        },
                    )
                ],
            }
        )
        move.action_post()

        # Get the move line
        move_line = move.line_ids.filtered(lambda l: l.account_id == self.account)[0]

        # Call the method
        vals = move_line._prepare_payment_line_vals(self.payment_order)

        # Check that communication_type is set to 'qrr'
        self.assertEqual(vals.get("communication_type"), "qrr")

        # Check that communication has spaces removed
        if vals.get("communication"):
            self.assertNotIn(" ", vals["communication"])

    def test_prepare_payment_line_vals_without_qr_iban(self):
        """Test _prepare_payment_line_vals without QR-IBAN"""
        # Create a partner bank without QR-IBAN
        partner_bank_no_qr = self.env["res.partner.bank"].create(
            {
                "bank_id": self.bank.id,
                "acc_number": "CH04 8914 4618 6435 6132 3",
                "partner_id": self.company.partner_id.id,
                "allow_out_payment": True,
            }
        )

        # Create a move with ISR reference but no QR-IBAN
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "partner_bank_id": partner_bank_no_qr.id,
                "payment_reference": "21 00000 00000 31394 71430 00901",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Product",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "account_id": self.account.id,
                        },
                    )
                ],
            }
        )
        move.action_post()

        # Get the move line
        move_line = move.line_ids.filtered(lambda l: l.account_id == self.account)[0]

        # Call the method
        vals = move_line._prepare_payment_line_vals(self.payment_order)

        # Check that communication_type is NOT set to 'qrr'
        self.assertNotEqual(vals.get("communication_type"), "qrr")

    def test_prepare_payment_line_vals_without_isr_ref(self):
        """Test _prepare_payment_line_vals without ISR reference"""
        # Create a move without ISR reference but with QR-IBAN
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "partner_bank_id": self.partner_bank.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Product",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "account_id": self.account.id,
                        },
                    )
                ],
            }
        )
        move.action_post()

        # Get the move line
        move_line = move.line_ids.filtered(lambda l: l.account_id == self.account)[0]

        # Call the method
        vals = move_line._prepare_payment_line_vals(self.payment_order)

        # Check that communication_type is NOT set to 'qrr'
        self.assertNotEqual(vals.get("communication_type"), "qrr")

    def test_prepare_payment_line_vals_normal_case(self):
        """Test _prepare_payment_line_vals for normal case without QR features"""
        # Create a move without ISR reference and without QR-IBAN
        partner_bank_normal = self.env["res.partner.bank"].create(
            {
                "bank_id": self.bank.id,
                "acc_number": "CH04 8914 4618 6435 6132 4",
                "partner_id": self.company.partner_id.id,
                "allow_out_payment": True,
            }
        )

        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "partner_bank_id": partner_bank_normal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Product",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "account_id": self.account.id,
                        },
                    )
                ],
            }
        )
        move.action_post()

        # Get the move line
        move_line = move.line_ids.filtered(lambda l: l.account_id == self.account)[0]

        # Call the method
        vals = move_line._prepare_payment_line_vals(self.payment_order)

        # Check that vals is returned (basic test)
        self.assertIsInstance(vals, dict)
        self.assertNotEqual(vals.get("communication_type"), "qrr")
