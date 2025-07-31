# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import os
from os.path import dirname, join

import requests
from lxml import etree
from vcr import VCR
from xmlunittest import XmlTestMixin

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class CommonCase(TransactionCase, XmlTestMixin):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.setUpBasicData()
        cls.setUpSaleData()
        cls.setUpInvoiceData()

    @classmethod
    def setUpBasicData(cls):
        cls.service = cls.env["ebill.postfinance.service"].create(
            {
                "name": "Postfinance Test Service",
                "use_test_service": True,
                "biller_id": os.getenv("BILLER_ID", "41101000001021209"),
                "username": os.getenv("POSTFINANCE_USER", "user"),
                "password": os.getenv("POSTFINANCE_PWD", "pwd"),
            }
        )
        cls.country = cls.env.ref("base.ch")
        cls.company = cls.env.ref("base.demo_company_ch")
        cls.env.user.company_id = cls.company
        cls.company.vat = "CHE-012.345.678"
        cls.company.name = "Camptocamp SA"
        cls.company.street = "StreetOne"
        cls.company.street2 = ""
        cls.company.zip = "1015"
        cls.company.city = "Lausanne"
        cls.company.partner_id.country_id = cls.country
        cls.company.email = "info@camptocamp.com"
        cls.company.phone = ""
        cls.bank = cls.env.ref("base.res_bank_1")
        cls.bank.bic = 777
        cls.tax7 = cls.env.ref(f"account.{cls.company.id}_vat_77")
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "bank_id": cls.bank.id,
                "acc_number": "CH04 8914 4618 6435 6132 2",
                "acc_holder_name": "AccountHolderName",
                "partner_id": cls.company.partner_id.id,
                "l10n_ch_qr_iban": "CH2130808001234567827",
            }
        )
        cls.payment_term = cls.env.ref("account.account_payment_term_advance_60days")
        cls.state = cls.env["res.country.state"].create(
            {"code": "RR", "name": "Fribourg", "country_id": cls.country.id}
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Test RAD Customer XML",
                "customer_rank": 1,
                "is_company": True,
                "street": "Teststrasse 100",
                "street2": "This is a very long street name that should be snapped",
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
                "postfinance_billerid": "41010198248040391",
                "state": "open",
                "postfinance_service_id": cls.service.id,
            }
        )
        cls.account = cls.env["account.account"].search(
            [("account_type", "=", "asset_receivable")],
            limit=1,
        )

    @classmethod
    def setUpSaleData(cls):
        cls.product = cls.env["product.product"].create(
            {"name": "Product Q & A", "list_price": 100.00, "default_code": "370003021"}
        )
        cls.product_long_name = cls.env["product.product"].create(
            {
                "name": "Product With a Very Long Name That Need To Be Truncated",
                "list_price": 0.00,
                "default_code": "370003022",
            }
        )
        cls.product.product_tmpl_id.invoice_policy = "order"
        cls.product_long_name.product_tmpl_id.invoice_policy = "order"
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

    @classmethod
    def setUpInvoiceData(cls):
        # Generate the invoice from the sale order
        cls.invoice = cls.sale._create_invoices()
        # And add some more lines on the invoice
        # One UX line and one not linked to a product and without VAT
        cls.invoice.update(
            {
                "line_ids": [
                    (0, 0, {"name": "A little note", "display_type": "line_note"}),
                    (
                        0,
                        0,
                        {
                            "name": "Phone support",
                            "quantity": 4.0,
                            "price_unit": 0,
                            # Force not tax on this line, for testing purpose
                            "tax_ids": [(5, 0, 0)],
                        },
                    ),
                ],
            }
        )
        cls.invoice.payment_reference = "210000000003139471430009017"
        cls.invoice.partner_bank_id = cls.partner_bank.id

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return cls._super_send(s, r, **kw)

    @staticmethod
    def compare_xml_line_by_line(content, expected):
        """This a quick way to check the diff line by line to ease debugging"""
        generated_line = [i.strip() for i in content.split(b"\n") if len(i.strip())]
        expected_line = [i.strip() for i in expected.split(b"\n") if len(i.strip())]
        number_of_lines = len(expected_line)
        for i in range(number_of_lines):
            if generated_line[i].strip() != expected_line[i].strip():
                return " || ".join(
                    [
                        f"Diff at {i}/{number_of_lines}",
                        f"Expected {expected_line[i]}",
                        f"Generated {generated_line[i]}",
                    ]
                )


def get_recorder(base_path=None, **kw):
    base_path = base_path or dirname(__file__)
    defaults = dict(
        record_mode="once",
        cassette_library_dir=join(base_path, "fixtures/cassettes"),
        path_transformer=VCR.ensure_suffix(".yaml"),
        match_on=["method", "path", "query"],
        filter_headers=["Authorization"],
        decode_compressed_response=True,
    )
    defaults.update(kw)
    return VCR(**defaults)


recorder = get_recorder()


def clean_xml(txt):
    return etree.canonicalize(txt.decode(), strip_text=True).encode()
