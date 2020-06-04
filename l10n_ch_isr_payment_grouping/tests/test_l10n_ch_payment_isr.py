# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time

from odoo import tools
from odoo.modules.module import get_resource_path
from odoo.tests import Form, common, tagged

ISR1 = "703192500010549027000209403"
ISR2 = "120000000000234478943216899"


@tagged("post_install", "-at_install")
class PaymentISR(common.TransactionCase):
    """Test grouping of payment by ISR reference"""

    def _load(self, module, *args):
        tools.convert_file(
            self.cr,
            "l10n_ch",
            get_resource_path(module, *args),
            {},
            "init",
            False,
            "test",
            self.registry._assertion_report,
        )

    def create_supplier_invoice(
        self, supplier, ref, currency_to_use="base.CHF", inv_date=None
    ):
        """ Generates a test invoice """
        f = Form(self.env["account.move"].with_context(default_type="in_invoice"))
        f.partner_id = supplier
        f.invoice_payment_ref = ref
        f.currency_id = self.env.ref(currency_to_use)
        f.invoice_date = inv_date or time.strftime("%Y") + "-12-22"
        with f.invoice_line_ids.new() as line:
            line.product_id = self.env.ref("product.product_product_4")
            line.quantity = 1
            line.price_unit = 42

        invoice = f.save()
        invoice.post()
        return invoice

    def create_bank_account(self, number, partner, bank=None):
        """ Generates a test res.partner.bank. """
        return self.env["res.partner.bank"].create(
            {"acc_number": number, "bank_id": bank.id, "partner_id": partner.id}
        )

    def create_isrb_account(self, number, partner):
        """ Generates a test res.partner.bank. """
        return self.env["res.partner.bank"].create(
            {
                "acc_number": partner.name + number,
                "l10n_ch_postal": number,
                "partner_id": partner.id,
            }
        )

    def setUp(self):
        super().setUp()
        self._load("account", "test", "account_minimal_test.xml")
        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        abs_bank = self.env["res.bank"].create(
            {"name": "Alternative Bank Schweiz", "bic": "ABSOCH22XXX"}
        )

        self.bank_journal_chf = self.env["account.journal"].create(
            {"name": "Bank", "type": "bank", "code": "BNK41"}
        )
        self.supplier_isrb1 = self.env["res.partner"].create({"name": "Supplier ISR 1"})
        self.create_isrb_account("01-162-8", self.supplier_isrb1)
        self.supplier_isrb2 = self.env["res.partner"].create({"name": "Supplier ISR 2"})
        self.create_isrb_account("01-162-8", self.supplier_isrb2)
        self.supplier_iban = self.env["res.partner"].create({"name": "Supplier IBAN"})
        self.create_bank_account(
            "CH61 0839 0107 6280 0100 0", self.supplier_iban, abs_bank
        )

    def _filter_vals_to_test(self, vals):
        return [
            (
                v["communication"],
                v["partner_id"],
                len(v["invoice_ids"][0][2]),
                v["amount"],
            )
            for v in sorted(vals, key=lambda i: (i["communication"], i["partner_id"]))
        ]

    def test_payment_isr_grouping(self):
        """Create multiple invoices to test grouping by partner and ISR

        """
        invoices = (
            self.create_supplier_invoice(self.supplier_isrb1, ISR1)
            | self.create_supplier_invoice(self.supplier_isrb1, ISR2)
            | self.create_supplier_invoice(
                self.supplier_isrb1, ISR2, inv_date=time.strftime("%Y") + "-12-23"
            )
            | self.create_supplier_invoice(self.supplier_isrb2, ISR2)
            | self.create_supplier_invoice(self.supplier_iban, "1234")
            | self.create_supplier_invoice(self.supplier_iban, "5678")
        )
        # create an invoice where ref is set instead of invoice_payment_ref
        inv_ref = self.create_supplier_invoice(self.supplier_isrb1, False)
        inv_ref.ref = ISR2
        invoices |= inv_ref
        inv_no_ref = self.create_supplier_invoice(self.supplier_iban, False)
        invoices |= inv_no_ref
        PaymentRegister = self.env["account.payment.register"]
        ctx = {"active_model": "account.move", "active_ids": invoices.ids}
        register = PaymentRegister.with_context(ctx).create({"group_payment": True})

        vals = register.get_payments_vals()
        self.assertEqual(len(vals), 4)
        expected_vals = [
            # ref, partner, invoice count, amount
            # 3 invoices #2, #3 and inv_ref grouped in one payment with a single ref
            (ISR2, self.supplier_isrb1.id, 3, 126.0),
            # different partner, different payment
            (ISR2, self.supplier_isrb2.id, 1, 42.0),
            # not ISR, standard grouping
            ("1234 5678 {}".format(inv_no_ref.name), self.supplier_iban.id, 3, 126.0,),
            # different ISR reference, different payment
            (ISR1, self.supplier_isrb1.id, 1, 42.0),
        ]
        to_test_vals = self._filter_vals_to_test(vals)
        self.assertEqual(to_test_vals, expected_vals)

    def test_payment_isr_grouping_single_supplier(self):
        """Test grouping of ISR on a single supplier

        No grouping of different ISR should apply

        """
        invoices = (
            self.create_supplier_invoice(self.supplier_isrb1, ISR1)
            | self.create_supplier_invoice(self.supplier_isrb1, ISR2)
            | self.create_supplier_invoice(
                self.supplier_isrb1, ISR2, inv_date=time.strftime("%Y") + "-12-23"
            )
        )
        PaymentRegister = self.env["account.payment.register"]
        ctx = {"active_model": "account.move", "active_ids": invoices.ids}
        register = PaymentRegister.with_context(ctx).create({"group_payment": True})

        vals = register.get_payments_vals()
        self.assertEqual(len(vals), 2)
        expected_vals = [
            # ref, partner, invoice count, amount
            # 2 invoices with same ISR are grouped
            (ISR2, self.supplier_isrb1.id, 2, 84.0),
            # the invoice with a different ISR makes a different payment
            (ISR1, self.supplier_isrb1.id, 1, 42.0),
        ]
        to_test_vals = self._filter_vals_to_test(vals)
        self.assertEqual(to_test_vals, expected_vals)

    def test_payment_isr_single_supplier(self):
        """Test no grouping of ISR on a single supplier

        No grouping on ISR should apply

        """
        invoices = (
            self.create_supplier_invoice(self.supplier_isrb1, ISR1)
            | self.create_supplier_invoice(self.supplier_isrb1, ISR2)
            | self.create_supplier_invoice(
                self.supplier_isrb1, ISR2, inv_date=time.strftime("%Y") + "-12-23"
            )
        )
        PaymentRegister = self.env["account.payment.register"]
        ctx = {"active_model": "account.move", "active_ids": invoices.ids}
        register = PaymentRegister.with_context(ctx).create({"group_payment": False})

        vals = register.get_payments_vals()
        self.assertEqual(len(vals), 3)
        expected_vals = [
            # no grouping expected
            # ref, partner, invoice count, amount
            (ISR2, self.supplier_isrb1.id, 1, 42.0),
            (ISR2, self.supplier_isrb1.id, 1, 42.0),
            (ISR1, self.supplier_isrb1.id, 1, 42.0),
        ]
        to_test_vals = self._filter_vals_to_test(vals)
        self.assertEqual(to_test_vals, expected_vals)

    def test_payment_non_isr_grouping_single_supplier(self):
        """Test grouping of non ISR on a single partner

        Grouping on free ref should apply

        """
        invoices = self.create_supplier_invoice(
            self.supplier_iban, "INV1"
        ) | self.create_supplier_invoice(self.supplier_iban, "INV2")
        PaymentRegister = self.env["account.payment.register"]
        ctx = {"active_model": "account.move", "active_ids": invoices.ids}
        register = PaymentRegister.with_context(ctx).create({"group_payment": True})

        vals = register.get_payments_vals()
        self.assertEqual(len(vals), 1)

        expected_vals = [
            # 2 invoices grouped in one payment
            # ref, partner, invoice count, amount
            ("INV1 INV2", self.supplier_iban.id, 2, 84.0)
        ]
        to_test_vals = self._filter_vals_to_test(vals)
        self.assertEqual(to_test_vals, expected_vals)

    def test_payment_non_isr_single_supplier(self):
        """Test no grouping of non ISR on a single partner

        No grouping on free ref applies

        """
        # This differs from v12 where an automatic grouping is done anyway
        # v13 respects the choice of the user
        invoices = self.create_supplier_invoice(
            self.supplier_iban, "INV1"
        ) | self.create_supplier_invoice(self.supplier_iban, "INV2")
        PaymentRegister = self.env["account.payment.register"]
        ctx = {"active_model": "account.move", "active_ids": invoices.ids}
        register = PaymentRegister.with_context(ctx).create({"group_payment": False})

        vals = register.get_payments_vals()
        self.assertEqual(len(vals), 2)
        expected_vals = [
            # no grouping expected
            # ref, partner, invoice count, amount
            ("INV1", self.supplier_iban.id, 1, 42.0),
            ("INV2", self.supplier_iban.id, 1, 42.0),
        ]
        to_test_vals = self._filter_vals_to_test(vals)
        self.assertEqual(to_test_vals, expected_vals)
