# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from functools import cache
from itertools import count

from lxml import etree

from odoo import models, release
from odoo.exceptions import UserError
from odoo.tools import file_path
from odoo.tools.xml_utils import cleanup_xml_node

from odoo.addons.base.models.res_bank import sanitize_account_number

TEMPLATE = "account_invoice_export_yellowbill.invoice_yellowbill"
XML_SCHEMA = "account_invoice_export_yellowbill/schemas/ybInvoice_V2.0.4.xsd"
DOCUMENT_TYPE = {"out_invoice": "BILL", "out_refund": "CREDITADVICE"}


@cache
def _get_xml_schema(path):
    """Compile the schema once: it is the same file for the whole process."""
    return etree.XMLSchema(file=path)


class AccountInvoiceYellowbill(models.AbstractModel):
    """Build the eBill YellowBill (ybInvoice V2.0.4) payload for an invoice.

    The YellowBill format is the invoice format of the Swiss eBill network. It
    is shared by every network partner (PostFinance, Conextrade, ...), so this
    model knows nothing about how the payload is transmitted: the caller passes
    the identifiers of its own contract and gets the XML back.
    """

    _name = "account.invoice.yellowbill"
    _description = "eBill YellowBill invoice builder"

    def _export_invoice(
        self,
        invoice,
        biller_id,
        ebill_account_id,
        transaction_id,
        pdf_data="",
        payment_type=None,
        lang=None,
    ):
        """Render the YellowBill XML for a single customer invoice.

        :param invoice: the ``account.move`` to export.
        :param biller_id: the biller identifier of the sender's eBill contract.
        :param ebill_account_id: the eBill account (payer) id of the customer.
        :param transaction_id: the identifier of this transmission.
        :param pdf_data: base64 encoded PDF, embedded as the bill appendix.
        :param payment_type: how the bill is to be paid. Deduced from the
            invoice when unset.
        :param lang: language to render the payload in, customer language if
            unset.
        :return: the payload, as a string.
        """
        invoice.ensure_one()
        if invoice.move_type not in DOCUMENT_TYPE:
            raise UserError(
                self.env._(
                    "%(name)s is not a customer invoice or credit note, "
                    "it cannot be exported as an eBill.",
                    name=invoice.display_name,
                )
            )
        lang = lang or invoice.partner_id.lang or self.env.lang
        values = self.with_context(lang=lang)._get_render_values(
            invoice,
            biller_id=biller_id,
            ebill_account_id=ebill_account_id,
            transaction_id=transaction_id,
            pdf_data=pdf_data,
            payment_type=payment_type,
        )
        payload = self.env["ir.qweb"]._render(TEMPLATE, values)
        # Optional elements are guarded in the template, so an empty node here
        # is one the schema requires (e.g. <URLBillDetails/>): keep it.
        node = cleanup_xml_node(payload, remove_blank_nodes=False)
        return etree.tostring(node, xml_declaration=True, encoding="utf-8").decode()

    def _check_invoice(self, invoice, payment_type=None):
        """Check that an invoice can be described by the format.

        Call this before exporting, from somewhere the failure can be reported
        to whoever can fix it: the schema can only report what is missing in
        terms of the document, not of the invoice.
        """
        payment_type = payment_type or self._get_payment_type(invoice)
        if payment_type == "iban" and not invoice.partner_bank_id:
            raise UserError(
                self.env._(
                    "%(name)s has no recipient bank account, so the eBill "
                    "cannot tell the customer how to pay it.",
                    name=invoice.display_name,
                )
            )

    def _get_render_values(
        self,
        invoice,
        biller_id,
        ebill_account_id,
        transaction_id,
        pdf_data="",
        payment_type=None,
    ):
        """Build the template values. This is the extension point of the format."""
        payment_type = payment_type or self._get_payment_type(invoice)
        lines = self._get_invoice_lines(invoice)
        orders = invoice.line_ids.sale_line_ids.order_id
        bank = invoice.partner_bank_id
        # A refund is reported with negated amounts.
        amount_sign = -1 if invoice.move_type == "out_refund" else 1
        # The delivery place is only reported when it differs from the customer.
        delivery = invoice.partner_shipping_id - invoice.partner_id
        # References to the order are only reported when the invoice has one.
        order = orders if len(orders) == 1 else orders.browse()
        return {
            "invoice": invoice,
            "biller": invoice.company_id,
            "customer": invoice.partner_id,
            "delivery": delivery,
            "bank": bank,
            "bank_account": sanitize_account_number(
                bank.l10n_ch_qr_iban or bank.acc_number or ""
            ),
            "biller_id": biller_id,
            "ebill_account_id": ebill_account_id,
            "transaction_id": transaction_id,
            "pdf_data": pdf_data,
            "payment_type": payment_type,
            "document_type": DOCUMENT_TYPE[invoice.move_type],
            # The format asks for the version of the software that issued it.
            "software_version": release.major_version,
            "language": (self.env.lang or "en")[:2],
            "order": order,
            "next_reference_position": self._get_reference_position_counter(),
            "line_vals_list": self._get_line_vals_list(lines),
            "tax_vals_list": self._get_tax_vals_list(invoice, amount_sign),
            "discount_vals_list": self._get_discount_vals_list(invoice),
            "total_tax": round(invoice.amount_tax, 6),
            "total_exclusive_tax": invoice.amount_untaxed * amount_sign,
            "total_inclusive_tax": invoice.amount_total * amount_sign,
            "total_paid": (invoice.amount_total - invoice.amount_residual)
            * amount_sign,
            "total_due": invoice.amount_residual * amount_sign,
            **self._get_date_vals(invoice, order),
        }

    def _get_payment_type(self, invoice):
        """How the bill is to be paid, deduced from what is billed.

        A refund is credited back to the customer, anything else is to be paid
        to us by bank transfer.
        """
        return "credit" if invoice.move_type == "out_refund" else "iban"

    def _get_invoice_lines(self, invoice):
        """Invoice lines to be reported.

        Lines that are only there for the layout (notes, sections) are left out.
        """
        return invoice.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )

    def _get_reference_position_counter(self):
        """Number every reference of the payload, in the order they appear.

        The numbering is shared by the header and the lines, and which
        references are reported is decided by the template, so the template is
        what advances the counter.
        """
        counter = count(1)
        return lambda: next(counter)

    def _get_date_vals(self, invoice, order):
        """Dates of the payload, formatted as the schema expects them.

        The bill is dated by its invoice date, which an invoice only carries
        once it is posted: an unposted one is dated today.
        """
        invoice_date = self._format_date(invoice.invoice_date)
        return {
            "delivery_date": invoice_date,
            "document_date": invoice_date,
            "achievement_start_date": invoice_date,
            "achievement_end_date": invoice_date,
            "order_date": self._format_date(order.date_order),
            "payment_due_date": self._format_date(
                invoice.invoice_date_due or invoice.invoice_date
            ),
        }

    def _get_line_vals_list(self, lines):
        return [self._get_line_vals(line) for line in lines]

    def _get_line_vals(self, line):
        return {
            "line": line,
            "product_description": (line.product_id.name or line.name or "")[:255],
            "quantity": line.quantity,
            "quantity_description": line.product_uom_id.name or "PCE",
            "amount_exclusive_tax": round(line.price_subtotal, 6),
            "amount_inclusive_tax": round(line.price_total, 6),
            "tax_vals": self._get_line_tax_vals(line),
        }

    def _get_line_tax_vals(self, line):
        """Only the first tax of the line is reported by the format."""
        tax = line.tax_ids[:1]
        if not tax:
            return {}
        return {
            "rate": round(tax.amount, 2),
            "amount": round(self._get_line_tax_amount(line, tax), 2),
            "base_exclusive_tax": round(line.price_subtotal, 6),
            "base_inclusive_tax": round(line.price_total, 6),
        }

    def _get_line_tax_amount(self, line, tax):
        """Amount of one tax of an invoice line, discount included."""
        if not tax:
            return 0.0
        price = line.price_unit * (1 - (line.discount or 0.0) / 100)
        result = tax.compute_all(
            price_unit=price,
            currency=line.move_id.currency_id,
            quantity=line.quantity,
            product=line.product_id,
            partner=line.move_id.partner_id,
        )
        return result["taxes"][0]["amount"]

    def _get_tax_vals_list(self, invoice, amount_sign):
        """Summarize the taxes of the invoice, one entry per rate."""
        vals_list = []
        for subtotal in invoice.tax_totals["subtotals"]:
            for tax_group in subtotal["tax_groups"]:
                tax_amount = tax_group["tax_amount"]
                base_amount = tax_group["base_amount"]
                # The rate is only available in the name of the group.
                rate = tax_group["group_name"].split()[-1:][0][:-1]
                vals_list.append(
                    {
                        "rate": rate or "0",
                        "amount": round(round(tax_amount, 2), 6) * amount_sign,
                        "base_exclusive_tax": round(base_amount, 6) * amount_sign,
                        "base_inclusive_tax": (
                            round(base_amount, 6) + round(tax_amount, 6)
                        )
                        * amount_sign,
                    }
                )
        return vals_list

    def _get_discount_vals_list(self, invoice):
        terms = invoice.invoice_payment_term_id
        if not terms.early_discount:
            return []
        return [{"days": terms.discount_days, "rate": terms.discount_percentage}]

    def _format_date(self, value):
        """Format a date as the schema expects it, today's date if unset."""
        return (value or datetime.now()).strftime("%Y-%m-%d")

    def _validate_payload(self, payload):
        """Check a payload, given as bytes or as a string, against the schema."""
        if not isinstance(payload, bytes):
            payload = payload.encode("utf-8")
        parser = etree.XMLParser(schema=_get_xml_schema(file_path(XML_SCHEMA)))
        try:
            etree.fromstring(payload, parser)
        except etree.XMLSyntaxError as ex:
            raise UserError(str(ex.error_log)) from ex
