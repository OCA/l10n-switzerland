# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
from string import Template

from freezegun import freeze_time
from xmlunittest import XmlTestMixin

from odoo.tests.common import SingleTransactionCase
from odoo.tools import file_open

from .common import compare_xml_line_by_line


@freeze_time("2019-06-07 09:06:00")
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
        cls.company.zip = "8888"
        cls.company.city = "TestCity"
        cls.company.partner_id.country_id = cls.country
        cls.bank = cls.env.ref("base.res_bank_1")
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
            }
        )
        cls.terms = cls.env.ref("account.account_payment_term_15days")
        cls.paynet = cls.env["paynet.service"].create(
            {
                "name": "Paynet Test Service",
                "use_test_service": True,
                "client_pid": os.getenv("PAYNET_ID", "52110726772852593"),
                "service_type": "b2c",
            }
        )
        cls.state = cls.env["res.country.state"].create(
            {"code": "RR", "name": "Fribourg", "country_id": cls.country.id}
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Test RAD Customer XML",
                "customer_rank": 1,
                "street": "Teststrasse 100",
                "city": "Fribourg",
                "zip": "1700",
                "country_id": cls.country.id,
                "state_id": cls.state.id,
            }
        )
        cls.contract = cls.env["ebill.payment.contract"].create(
            {
                "partner_id": cls.customer.id,
                "paynet_account_number": "41010198248040391",
                "state": "open",
                "paynet_service_id": cls.paynet.id,
                "payment_type": "esr",
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
        cls.product = cls.env["product.template"].create(
            {"name": "Product One", "list_price": 100.00}
        )
        cls.invoice_1 = cls.env["account.move"].create(
            {
                "partner_id": cls.customer.id,
                # 'account_id': cls.account.id,
                "invoice_partner_bank_id": cls.partner_bank.id,
                "invoice_payment_term_id": cls.terms.id,
                "type": "out_invoice",
                "transmit_method_id": cls.env.ref(
                    "ebill_paynet.paynet_transmit_method"
                ).id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": cls.account.id,
                            "product_id": cls.product.product_variant_ids[:1].id,
                            "name": "Product 1",
                            "quantity": 4.0,
                            "price_unit": 123.00,
                            "tax_ids": [(4, cls.tax7.id, 0)],
                        },
                    )
                ],
            }
        )

    def test_icref_generation(self):
        """ """
        message = self.invoice_1.create_paynet_message()
        message.ic_ref = message._get_ic_ref()
        self.assertEqual(message.ic_ref, "SA%012d" % message.id)

    def test_invoice(self):
        """ Check XML payload genetated for an invoice."""
        self.invoice_1.name = "INV_TEST_01"
        # self.invoice_1.action_invoice_sent()
        # TODO set a due date different to create date
        # self.invoice_1.date_due = '2019-07-01'
        self.invoice_1.state = "posted"
        message = self.invoice_1.create_paynet_message()
        message.payload = message._generate_payload()
        # Remove the PDF file data from the XML to ease testing
        lines = message.payload.splitlines()
        for pos, line in enumerate(lines):
            if line.find("Back-Pack") != -1:
                lines.pop(pos + 1)
                break
        payload = "\n".join(lines).encode("utf8")
        # self.assertXmlDocument(payload)
        # Prepare the XML file that is expected
        expected_tmpl = Template(
            file_open("ebill_paynet/tests/examples/invoice_1.xml").read()
        )
        expected = expected_tmpl.substitute(IC_REF=message.ic_ref).encode("utf8")
        self.assertFalse(compare_xml_line_by_line(payload, expected))
        self.assertXmlEquivalentOutputs(payload, expected)
