# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
from os.path import dirname, join

from vcr import VCR
from xmlunittest import XmlTestMixin

from odoo.tests.common import SavepointCase


class CommonCase(SavepointCase, XmlTestMixin):
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
        # Set a delivery tracking number
        cls.pickings = cls.sale.order_line.move_ids.mapped("picking_id")
        cls.pickings[0].carrier_tracking_ref = "track_me_if_you_can"
        # Generate the invoice from the sale order
        cls.invoice = cls.sale._create_invoices()
        # And add some more lines on the invoice
        # One UX line and one not linked to a product
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
                            # Set zero, avoiding error with accounting ?!
                            "price_unit": 0,
                            "account_id": cls.at_receivable.id,
                            # "tax_id": [(4, cls.tax7.id, 0)],
                        },
                    ),
                ],
            }
        )
        cls.invoice.action_post()
        cls.invoice.payment_reference = "1234567890"
        cls.invoice.partner_bank_id = cls.partner_bank.id

    @staticmethod
    def compare_xml_line_by_line(content, expected):
        """This a quick way to check the diff line by line to ease debugging"""
        generated_line = [i.strip() for i in content.split(b"\n") if len(i.strip())]
        expected_line = [i.strip() for i in expected.split(b"\n") if len(i.strip())]
        number_of_lines = len(expected_line)
        for i in range(number_of_lines):
            if generated_line[i].strip() != expected_line[i].strip():
                return "Diff at {}/{} || Expected {}  || Generated {}".format(
                    i,
                    number_of_lines,
                    expected_line[i],
                    generated_line[i],
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
