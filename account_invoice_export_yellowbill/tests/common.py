# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon

BILLER_ID = "41101000001021209"
EBILL_ACCOUNT_ID = "41010198248040391"


class CommonCase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.builder = cls.env["account.invoice.yellowbill"]
        cls.setUpBasicData()
        cls.setUpSaleData()
        cls.setUpInvoiceData()

    @classmethod
    def setUpBasicData(cls):
        cls.country = cls.quick_ref("base.ch")
        cls.company = cls.env["res.company"].create(
            {
                "name": "Camptocamp SA",
                "country_id": cls.country.id,
            }
        )
        cls.env["account.chart.template"].try_loading(
            "ch", company=cls.company, install_demo=False
        )
        cls.env.user.company_id = cls.company
        cls.company.currency_id = cls.quick_ref("base.CHF")
        cls.company.vat = "CHE-012.345.678"
        cls.company.street = "StreetOne"
        cls.company.street2 = ""
        cls.company.zip = "1015"
        cls.company.city = "Lausanne"
        cls.company.partner_id.country_id = cls.country
        cls.company.email = "info@camptocamp.com"
        cls.company.phone = ""
        cls.bank = cls.quick_ref("base.res_bank_1")
        cls.bank.bic = "777"
        cls.tax7 = cls.quick_ref(f"account.{cls.company.id}_vat_77")
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "bank_id": cls.bank.id,
                "acc_number": "CH04 8914 4618 6435 6132 2",
                "acc_holder_name": "AccountHolderName",
                "partner_id": cls.company.partner_id.id,
                "l10n_ch_qr_iban": "CH2130808001234567827",
            }
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test CHF",
                "currency_id": cls.company.currency_id.id,
                "company_id": cls.company.id,
            }
        )
        cls.payment_term = cls.quick_ref("account.account_payment_term_advance_60days")
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
                "pricelist_id": cls.pricelist.id,
                "client_order_ref": "CustomerRef",
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "name": cls.product.name,
                            "product_uom_qty": 4.0,
                            "price_unit": 123.0,
                            "tax_ids": [Command.link(cls.tax7.id)],
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.product_long_name.id,
                            "name": cls.product_long_name.name,
                            "product_uom_qty": 1.0,
                            "price_unit": 0.0,
                            "tax_ids": [Command.link(cls.tax7.id)],
                        }
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
                    Command.create(
                        {"name": "A little note", "display_type": "line_note"}
                    ),
                    Command.create(
                        {
                            "name": "Phone support",
                            "quantity": 4.0,
                            "price_unit": 0,
                            # Force not tax on this line, for testing purpose
                            "tax_ids": [Command.clear()],
                        }
                    ),
                ],
            }
        )
        cls.invoice.payment_reference = "210000000003139471430009017"
        cls.invoice.partner_bank_id = cls.partner_bank.id


def clean_xml(txt):
    """Canonicalize a payload, so only its structure and values are compared."""
    clean = etree.canonicalize(txt, strip_text=True).encode()
    return etree.tostring(etree.fromstring(clean), pretty_print=True)


def drop_appendix_document(txt):
    """Drop the embedded PDF node, its content is not what we assert on."""
    node = etree.fromstring(txt.encode("utf-8"))
    for document in node.findall("./Body/Appendix/Document"):
        document.getparent().remove(document)
    return etree.tostring(node).decode()


def compare_xml_line_by_line(content, expected):
    """A quick way to check the diff line by line, to ease debugging."""
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
