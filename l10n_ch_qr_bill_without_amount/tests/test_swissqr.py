# Copyright 2024 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import time

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install_l10n", "post_install", "-at_install")
class TestSwissQR(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref="l10n_ch.l10nch_chart_template"):
        super().setUpClass(chart_template_ref=chart_template_ref)

    def setUp(self):
        super(TestSwissQR, self).setUp()
        # Activate SwissQR in Swiss invoices
        self.env["ir.config_parameter"].create(
            {"key": "l10n_ch.print_qrcode", "value": "1"}
        )
        self.customer = self.env["res.partner"].create(
            {
                "name": "Partner",
                "street": "Route de Berne 41",
                "street2": "",
                "zip": "1000",
                "city": "Lausanne",
                "country_id": self.env.ref("base.ch").id,
            }
        )
        self.env.user.company_id.partner_id.write(
            {
                "street": "Route de Berne 88",
                "street2": "",
                "zip": "2000",
                "city": "Neuchâtel",
                "country_id": self.env.ref("base.ch").id,
            }
        )
        self.product = self.env["product.product"].create(
            {
                "name": "Product 1",
            }
        )
        self.env["res.partner.bank"].create(
            {
                "acc_number": "CH21 3080 8001 2345 6782 7",
                "partner_id": self.env.user.company_id.partner_id.id,
            }
        )
        bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", self.env.company.id)], limit=1
        )
        bank_journal.invoice_reference_model = "ch"

        self.payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "Test Payment Mode",
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "bank_account_link": "fixed",
                "company_id": self.env.company.id,
                "fixed_journal_id": bank_journal.id,
                "qr_bill_without_amount": True,
            }
        )
        self.payment_mode.payment_method_id.bank_account_required = True

    def test_swissqr_generated_without_amount(self):
        account = self.env["account.account"].search(
            [("account_type", "=", "asset_current")], limit=1
        )
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.customer.id,
                "payment_mode_id": self.payment_mode.id,
                "currency_id": self.env.ref("base.CHF").id,
                "date": time.strftime("%Y") + "-12-22",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "account_id": account.id,
                            "quantity": 1,
                            "price_unit": 42.0,
                        },
                    )
                ],
            }
        )

        params = invoice.partner_bank_id._l10n_ch_get_qr_vals(
            42.0, invoice.currency_id, invoice.partner_id, invoice.payment_reference, ""
        )
        self.assertEqual(params[18], "42.00")
        params = invoice.with_context(
            qr_bill_without_amount={invoice.name: True}
        ).partner_bank_id._l10n_ch_get_qr_vals(
            42.0, invoice.currency_id, invoice.partner_id, invoice.name, ""
        )
        self.assertEqual(params[18], "")
