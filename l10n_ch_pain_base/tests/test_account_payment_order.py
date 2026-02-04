# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from lxml import etree

from odoo.tests.common import TransactionCase


class TestAccountPaymentOrder(TransactionCase):
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

        # Create bank account
        cls.bank = cls.env["res.bank"].create(
            {
                "name": "Test Bank",
                "bic": "POFICHBEXXX",
            }
        )

        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "bank_id": cls.bank.id,
                "acc_number": "CH04 8914 4618 6435 6132 2",
                "partner_id": cls.company.partner_id.id,
                "l10n_ch_qr_iban": "CH2130808001234567827",
                "allow_out_payment": True,
            }
        )

        # Create payment method with Swiss PAIN flavor
        cls.payment_method_ch = cls.env["account.payment.method"].create(
            {
                "name": "Swiss PAIN Credit Transfer",
                "code": "ch_pain_credit",
                "payment_type": "outbound",
            }
        )

        cls.payment_method_sepa = cls.env["account.payment.method"].create(
            {
                "name": "SEPA Credit Transfer",
                "code": "sepa_credit",
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
        # Create a sale journal
        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Test Sale Journal",
                "code": "TSALE",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )

        # Create payment mode
        cls.payment_mode_ch = cls.env["account.payment.mode"].create(
            {
                "name": "Swiss PAIN Payment Mode",
                "payment_method_id": cls.payment_method_ch.id,
                "company_id": cls.company.id,
                "fixed_journal_id": cls.journal.id,
                "bank_account_link": "fixed",
            }
        )

        cls.payment_mode_sepa = cls.env["account.payment.mode"].create(
            {
                "name": "SEPA Payment Mode",
                "payment_method_id": cls.payment_method_sepa.id,
                "company_id": cls.company.id,
                "fixed_journal_id": cls.journal.id,
                "bank_account_link": "fixed",
            }
        )

        # Create payment order
        cls.payment_order_ch = cls.env["account.payment.order"].create(
            {
                "payment_mode_id": cls.payment_mode_ch.id,
                "journal_id": cls.journal.id,
            }
        )

        cls.payment_order_sepa = cls.env["account.payment.order"].create(
            {
                "payment_mode_id": cls.payment_mode_sepa.id,
                "journal_id": cls.journal.id,
            }
        )

    def test_is_ch_pain_flavor(self):
        """Test the _is_ch_pain_flavor method"""
        # Test Swiss PAIN Credit Transfer
        self.assertTrue(
            self.payment_order_ch._is_ch_pain_flavor("pain.001.001.03.ch.02")
        )
        # Test Swiss PAIN Direct Debit
        self.assertTrue(
            self.payment_order_ch._is_ch_pain_flavor("pain.008.001.02.ch.01")
        )
        # Test non-Swiss PAIN flavor
        self.assertFalse(self.payment_order_ch._is_ch_pain_flavor("pain.001.001.03"))
        # Test None
        self.assertFalse(self.payment_order_ch._is_ch_pain_flavor(None))

    def test_compute_sepa_final_hook_ch_flavor(self):
        """Test compute_sepa_final_hook for Swiss PAIN flavor"""
        # Swiss PAIN should not be SEPA
        with patch.object(
            type(self.payment_method_ch), "pain_version", new_callable=PropertyMock
        ) as mock_pain_version:
            mock_pain_version.return_value = "pain.001.001.03.ch.02"
            result = self.payment_order_ch.compute_sepa_final_hook(True)
            self.assertFalse(result)

    def test_compute_sepa_final_hook_sepa_flavor(self):
        """Test compute_sepa_final_hook for non-Swiss PAIN flavor"""
        # Non-Swiss PAIN can be SEPA
        result = self.payment_order_sepa.compute_sepa_final_hook(True)
        self.assertTrue(result)

    def test_generate_pain_nsmap_ch_flavor(self):
        """Test generate_pain_nsmap for Swiss PAIN flavor"""
        with patch.object(
            type(self.payment_method_ch), "pain_version", new_callable=PropertyMock
        ) as mock_pain_version:
            mock_pain_version.return_value = "pain.001.001.03.ch.02"
            nsmap = self.payment_order_ch.generate_pain_nsmap()
            expected_url = (
                "http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd"
            )
            self.assertIn(None, nsmap)
            self.assertEqual(nsmap[None], expected_url)

    def test_generate_pain_nsmap_non_ch_flavor(self):
        """Test generate_pain_nsmap for non-Swiss PAIN flavor"""
        nsmap = self.payment_order_sepa.generate_pain_nsmap()
        # Should call super and return standard namespace
        self.assertIn(None, nsmap)
        # Should not be the Swiss namespace
        self.assertNotIn("six-interbank-clearing.com", nsmap.get(None, ""))

    def test_generate_pain_attrib_ch_flavor(self):
        """Test generate_pain_attrib for Swiss PAIN flavor"""
        with patch.object(
            type(self.payment_method_ch), "pain_version", new_callable=PropertyMock
        ) as mock_pain_version:
            mock_pain_version.return_value = "pain.001.001.03.ch.02"
            attrib = self.payment_order_ch.generate_pain_attrib()
            self.assertIn(
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", attrib
            )
            schema_location = attrib[
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
            ]
            self.assertIn("pain.001.001.03.ch.02.xsd", schema_location)

    def test_generate_pain_attrib_non_ch_flavor(self):
        """Test generate_pain_attrib for non-Swiss PAIN flavor"""
        attrib = self.payment_order_sepa.generate_pain_attrib()
        # Should call super and return standard attributes
        if attrib:
            self.assertNotIn("six-interbank-clearing.com", str(attrib))

    def test_generate_start_payment_info_block_ch_flavor(self):
        """Test generate_start_payment_info_block for Swiss PAIN flavor"""
        with patch.object(
            type(self.payment_method_ch), "pain_version", new_callable=PropertyMock
        ) as mock_pain_version:
            mock_pain_version.return_value = "pain.001.001.03.ch.02"
            parent_node = etree.Element("root")
            gen_args = {
                "pain_flavor": "pain.001.001.03.ch.02",
                "payment_method": "ch_pain_credit",
            }

            self.payment_order_ch.generate_start_payment_info_block(
                parent_node,
                payment_info_ident="name",
                priority=None,
                local_instrument=None,
                category_purpose=None,
                sequence_type=None,
                requested_date=None,
                eval_ctx={"name": "PMT-1"},
                gen_args=gen_args,
            )

            # Check that gen_args were modified correctly
            self.assertEqual(gen_args.get("local_instrument_type"), "proprietary")
            self.assertFalse(gen_args.get("structured_remittance_issuer"))

    def test_generate_remittance_info_block_qrr(self):
        """Test generate_remittance_info_block for QRR communication"""
        # Create a partner for the payment
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create account for the move
        account = self.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "TEST001",
                "account_type": "asset_receivable",
                "company_id": self.company.id,
            }
        )

        # Create a move with ISR reference
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "company_id": self.company.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Line",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "account_id": account.id,
                        },
                    )
                ],
            }
        )

        # Create payment line with QRR communication type
        payment_line = self.env["account.payment.line"].create(
            {
                "order_id": self.payment_order_ch.id,
                "partner_id": partner.id,
                "communication": "210000000003139471430009017",
                "communication_type": "qrr",
                "amount_currency": 100.0,
                "currency_id": self.company.currency_id.id,
                "move_line_id": move.line_ids.filtered(
                    lambda l: l.account_id == account
                )[0].id,
            }
        )

        # Create a mock payment line group
        line_group = SimpleNamespace(
            payment_line_ids=payment_line,
            move_line_id=payment_line.move_line_id,
        )

        # Test the remittance info block generation
        parent_node = etree.Element("root")
        gen_args = {}

        result = self.payment_order_ch.generate_remittance_info_block(
            parent_node, line_group, gen_args
        )

        # Check that the method returned True (indicating it handled the block)
        self.assertTrue(result)

        # Check the XML structure
        rmtinf = parent_node.find("RmtInf")
        self.assertIsNotNone(rmtinf)

        strd = rmtinf.find("Strd")
        self.assertIsNotNone(strd)

        cdtrref_info = strd.find("CdtrRefInf")
        self.assertIsNotNone(cdtrref_info)

        tp = cdtrref_info.find("Tp")
        self.assertIsNotNone(tp)

        cd_or_prtry = tp.find("CdOrPrtry")
        self.assertIsNotNone(cd_or_prtry)

        prtry = cd_or_prtry.find("Prtry")
        self.assertIsNotNone(prtry)
        self.assertEqual(prtry.text, "QRR")

        ref = cdtrref_info.find("Ref")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.text, "210000000003139471430009017")

    def test_generate_remittance_info_block_non_qrr(self):
        """Test generate_remittance_info_block for non-QRR communication"""
        # Create a partner for the payment
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create account for the move
        account = self.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "TEST002",
                "account_type": "asset_receivable",
                "company_id": self.company.id,
            }
        )

        # Create a move
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "company_id": self.company.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Line",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "account_id": account.id,
                        },
                    )
                ],
            }
        )

        # Create payment line with normal communication type
        payment_line = self.env["account.payment.line"].create(
            {
                "order_id": self.payment_order_ch.id,
                "partner_id": partner.id,
                "communication": "Normal communication",
                "communication_type": "normal",
                "amount_currency": 100.0,
                "currency_id": self.company.currency_id.id,
                "move_line_id": move.line_ids.filtered(
                    lambda l: l.account_id == account
                )[0].id,
            }
        )

        # Create a mock payment line group
        line_group = SimpleNamespace(
            payment_line_ids=payment_line,
            name="Test Line Group",
            payment_reference="Test Reference",
        )

        # Test the remittance info block generation - should call super
        parent_node = etree.Element("root")
        gen_args = {}

        # This should call super and potentially return something different
        # We just check it doesn't fail
        result = self.payment_order_ch.generate_remittance_info_block(
            parent_node, line_group, gen_args
        )

        # Result might be True or False depending on parent implementation
        # Just ensure no exception was raised
        self.assertIsNotNone(result)
