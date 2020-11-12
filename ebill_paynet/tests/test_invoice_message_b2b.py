# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
from string import Template

from freezegun import freeze_time
from xmlunittest import XmlTestMixin

from odoo.tests.common import SingleTransactionCase
from odoo.tools import file_open

from .common import compare_xml_line_by_line


@freeze_time("2019-06-21 09:06:00")
class TestInvoiceMessage(SingleTransactionCase, XmlTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.country = cls.env.ref("base.ch")
        cls.company = cls.env.user.company_id
        cls.company.vat = "CHE-012.345.678"
        cls.company.name = "Camptocamp SA"
        cls.company.street = "StreetOne"
        cls.company.street2 = ""
        cls.company.zip = "1015"
        cls.company.city = "Lausanne"
        cls.company.partner_id.country_id = cls.country

        cls.bank = cls.env.ref("base.res_bank_1")
        cls.bank.clearing = 777
        cls.tax7 = cls.env["account.tax"].create(
            {
                "name": "Test tax",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": "7.7",
                "tax_group_id": cls.env.ref("l10n_ch.tax_group_tva_77").id,
            }
        )
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "bank_id": cls.bank.id,
                "acc_number": "300.300.300",
                "acc_holder_name": "AccountHolderName",
                "partner_id": cls.company.partner_id.id,
                "l10n_ch_qr_iban": "CH21 3080 8001 2345 6782 7",
            }
        )
        cls.terms = cls.env.ref("account.account_payment_term_15days")
        cls.paynet = cls.env["paynet.service"].create(
            {
                "name": "Paynet Test Service",
                "use_test_service": True,
                "client_pid": os.getenv("PAYNET_ID", "52110726772852593"),
                "service_type": "b2b",
            }
        )
        cls.state = cls.env["res.country.state"].create(
            {"code": "RR", "name": "Fribourg", "country_id": cls.country.id}
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Test RAD Customer XML",
                "customer_rank": 1,
                "is_company": True,
                "street": "Teststrasse 100",
                "city": "Fribourg",
                "zip": "1700",
                "country_id": cls.country.id,
                "state_id": cls.state.id,
            }
        )
        cls.customer_delivery = cls.env["res.partner"].create(
            {
                "name": "The Shed in the yard",
                "street": "Teststrasse 102",
                "city": "Fribourg",
                "zip": "1700",
                "parent_id": cls.customer.id,
                "type": "delivery",
            }
        )
        cls.contract = cls.env["ebill.payment.contract"].create(
            {
                "partner_id": cls.customer.id,
                "paynet_account_number": "41010198248040391",
                "state": "open",
                "paynet_service_id": cls.paynet.id,
                "payment_type": "qr",
            }
        )
        cls.account = cls.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_revenue").id,
                )
            ],
            limit=1,
        )
        cls.at_receivable = cls.env["account.account.type"].create(
            {
                "name": "Test receivable account",
                "type": "receivable",
                "internal_group": "asset",
            }
        )
        cls.a_receivable = cls.env["account.account"].create(
            {
                "name": "Test receivable account",
                "code": "TEST_RA",
                "user_type_id": cls.at_receivable.id,
                "reconcile": True,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Product One", "list_price": 100.00, "default_code": "370003021"}
        )
        cls.product_long_name = cls.env["product.product"].create(
            {
                "name": "Product With a Very Long Name That Need To Be Truncated",
                "list_price": 0.00,
                "default_code": "370003022",
            }
        )
        cls.sale = cls.env["sale.order"].create(
            {
                "name": "Order123",
                "partner_id": cls.customer.id,
                "partner_shipping_id": cls.customer_delivery.id,
                "client_order_ref": "CustomerRef",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "name": cls.product.name,
                            "product_uom_qty": 4.0,
                            "price_unit": 123.0,
                            "tax_id": [(4, cls.tax7.id, 0)],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_long_name.id,
                            "name": cls.product_long_name.name,
                            "product_uom_qty": 1.0,
                            "price_unit": 0.0,
                            "tax_id": [(4, cls.tax7.id, 0)],
                        },
                    ),
                ],
            }
        )
        cls.sale.action_confirm()
        cls.sale.date_order = "2019-06-01"
        cls.invoice = cls.sale._create_invoices()
        cls.invoice.invoice_payment_ref = "1234567890"
        cls.invoice.invoice_partner_bank_id = cls.partner_bank.id

    def test_invoice(self):
        """ Check XML payload genetated for an invoice."""
        self.invoice.name = "INV_TEST_01"
        # self.invoice_1.action_invoice_sent()
        # TODO set a due date different to create date
        # self.invoice_1.date_due = '2019-07-01'
        self.invoice.state = "posted"
        message = self.invoice.create_paynet_message()
        message.payload = message._generate_payload()
        # Remove the PDF file data from the XML to ease testing
        lines = message.payload.splitlines()
        for pos, line in enumerate(lines):
            if line.find("Back-Pack") != -1:
                lines.pop(pos)
                break
        payload = "\n".join(lines).encode("utf8")
        self.assertXmlDocument(payload)
        # Prepare the XML file that is expected
        expected_tmpl = Template(
            file_open("ebill_paynet/tests/examples/invoice_b2b.xml").read()
        )
        expected = expected_tmpl.substitute(IC_REF=message.ic_ref).encode("utf8")
        # Remove the comments in the expected xml
        expected_nocomment = [
            line
            for line in expected.split(b"\n")
            if not line.lstrip().startswith(b"<!--")
        ]
        expected_nocomment = b"\n".join(expected_nocomment)
        self.assertFalse(compare_xml_line_by_line(payload, expected_nocomment))
        self.assertXmlEquivalentOutputs(payload, expected_nocomment)
