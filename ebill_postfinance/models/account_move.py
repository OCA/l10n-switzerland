# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

import odoo
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("transmit_method_id")
    def _compute_partner_bank_id(self):  # pylint: disable=missing-return
        super()._compute_partner_bank_id()
        for rec in self:
            pf_partner_bank = rec._get_postfinance_partner_bank()
            if pf_partner_bank:
                rec.partner_bank_id = pf_partner_bank

    def _get_postfinance_partner_bank(self):
        if self.move_type not in ("out_invoice", "out_refund"):
            return
        postfinance_method = self.env.ref(
            "ebill_postfinance.postfinance_transmit_method"
        )
        if self.transmit_method_id == postfinance_method:
            contract = self.partner_id.get_active_contract(self.transmit_method_id)
            if contract:
                return contract.postfinance_service_id.partner_bank_id

    def _export_invoice(self):
        """Export invoice with the help of account_invoice_export module."""
        postfinance_method = self.env.ref(
            "ebill_postfinance.postfinance_transmit_method"
        )
        if self.transmit_method_id != postfinance_method:
            return super()._export_invoice()
        message = self.create_postfinance_ebill()
        if not message:
            raise UserError(self.env._("Error generating postfinance eBill"))
        message.send_to_postfinance()
        self.invoice_exported = True
        return f"Postfinance invoice generated and in state {message.state}"

    def create_postfinance_ebill(self):
        """Generate the message record for an invoice."""
        self.ensure_one()
        contract = self.partner_id.get_active_contract(self.transmit_method_id)
        if not contract:
            return
        # Generate PDf to be send
        pdf_data = []
        # When test are run, pdf are not generated, so use an empty pdf
        pdf = b""
        report_names = ["account.report_invoice"]
        payment_type = ""
        if self.move_type == "out_invoice":
            payment_type = "iban"
            if contract.payment_type == "qr":
                report_names.append("l10n_ch.qr_report_main")
        elif self.move_type == "out_refund":
            payment_type = "credit"
        for report_name in report_names:
            # r = self.env["ir.actions.report"]._get_report_from_name(report_name)
            pdf_content, _ = self.env["ir.actions.report"]._render(
                report_name, [self.id]
            )
            # pdf_content, _ = r._render([self.id])
            pdf_data.append(pdf_content)
        if not odoo.tools.config["test_enable"]:
            if len(pdf_data) > 1:
                pdf = merge_pdf(pdf_data)
            elif len(pdf_data) == 1:
                pdf = pdf_data[0]
        message = self.env["ebill.postfinance.invoice.message"].create(
            {
                "service_id": contract.postfinance_service_id.id,
                "invoice_id": self.id,
                "ebill_account_number": contract.postfinance_billerid,
                "payment_type": payment_type,
                "ebill_payment_contract_id": contract.id,
            }
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": "postfinance ebill",
                "type": "binary",
                "datas": base64.b64encode(pdf).decode("ascii"),
                "res_model": "ebill.postfinance.invoice.message",
                "res_id": message.id,
                "mimetype": "application/x-pdf",
            }
        )
        message.attachment_id = attachment.id
        return message

    def postfinance_invoice_line_ids(self):
        """Filter invoice line to be included in XML message.

        Invoicing line that are UX based (notes, sections) are removed.

        """
        self.ensure_one()
        return self.invoice_line_ids.filtered(lambda r: r.display_type == "product")

    def get_postfinance_other_reference(self):
        """Allows glue module to insert <OTHER-REFERENCE> in the <HEADER>

        Add to the list ref, object strucutred like this:

            {'type': other reference allowed types,
             'no': the content of <Reference-No> desired
            }
        """
        self.ensure_one()
        return []

    def log_invoice_accepted_by_system(self):
        """ """
        self.activity_feedback(
            ["ebill_postfinance.mail_activity_dws_error"],
            feedback="It worked on a later try",
        )
        self.message_post(body=self.env._("Invoice accepted by the Postfinance system"))
        self.invoice_export_confirmed = True

    def log_invoice_refused_by_system(self):
        """ """
        activity_type = "ebill_postfinance.mail_activity_dws_error"
        activity = self.activity_reschedule(
            [activity_type], date_deadline=fields.Date.today()
        )
        values = {}
        if not activity:
            message = self.env.ref("ebill_postfinance.rejected_invoice")._render(
                values=values
            )
            activity = self.activity_schedule(
                activity_type, summary="Invoice rejected by Postfinance", note=message
            )
