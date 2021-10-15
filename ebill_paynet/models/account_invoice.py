# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

import odoo
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = "account.move"

    @api.onchange("partner_id", "company_id")
    def _transmit_method_partner_change(self):
        super()._transmit_method_partner_change()
        if self.move_type not in ("out_invoice", "out_refund"):
            return
        paynet_method = self.env.ref("ebill_paynet.paynet_transmit_method")
        if self.transmit_method_id == paynet_method:
            contract = self.partner_id.get_active_contract(self.transmit_method_id)
            if contract:
                self.invoice_partner_bank_id = (
                    contract.paynet_service_id.partner_bank_id
                )

    def _export_invoice(self):
        """Export invoice with the help of account_invoice_export module."""
        paynet_method = self.env.ref("ebill_paynet.paynet_transmit_method")
        if self.transmit_method_id != paynet_method:
            return super()._export_invoice()
        message = self.create_paynet_message()
        if not message:
            raise UserError(_("Error generating Paynet message"))
        message.send_to_paynet()
        self.invoice_exported = True
        return "Paynet invoice generated and in state {}".format(message.state)

    def create_paynet_message(self):
        """Generate the paynet message for an invoice."""
        self.ensure_one()
        contract = self.partner_id.get_active_contract(self.transmit_method_id)
        if not contract:
            return
        # Generate PDf to be send
        pdf_data = []
        report_names = ["account.report_invoice"]
        if contract.payment_type == "qr":
            report_names.append("l10n_ch.qr_report_main")
        elif contract.payment_type == "isr":
            report_names.append("l10n_ch.isr_report_main")
        for report_name in report_names:
            r = self.env["ir.actions.report"]._get_report_from_name(report_name)
            pdf_content, _ = r._render([self.id])
            pdf_data.append(pdf_content)
        if not odoo.tools.config["test_enable"]:
            pdf = merge_pdf(pdf_data)
        else:
            # When test are run, pdf are not generated, so use an empty pdf
            pdf = b""

        message = self.env["paynet.invoice.message"].create(
            {
                "service_id": contract.paynet_service_id.id,
                "invoice_id": self.id,
                "ebill_account_number": contract.paynet_account_number,
                "payment_type": contract.payment_type,
            }
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": "paynet ebill",
                "type": "binary",
                "datas": base64.b64encode(pdf).decode("ascii"),
                "res_model": "paynet.invoice.message",
                "res_id": message.id,
                "mimetype": "application/x-pdf",
            }
        )
        message.attachment_id = attachment.id
        return message

    def paynet_invoice_line_ids(self):
        """Filter invoice line to be included in XML message.

        Invoicing line that are UX based (notes, sections) are removed.

        """
        self.ensure_one()
        return self.invoice_line_ids.filtered(lambda r: not r.display_type)

    def get_paynet_other_reference(self):
        """Allows glue module to insert <OTHER-REFERENCE> in paynet <HEADER>

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
            ["ebill_paynet.mail_activity_dws_error"],
            feedback="It worked on a later try",
        )
        self.message_post(body=_("Invoice accepted by the Paynet system"))
        self.invoice_export_confirmed = True

    def log_invoice_refused_by_system(self):
        """ """
        activity_type = "ebill_paynet.mail_activity_dws_error"
        activity = self.activity_reschedule(
            [activity_type], date_deadline=fields.Date.today()
        )
        values = {}
        if not activity:
            message = self.env.ref("ebill_paynet.dws_reject_invoice")._render(
                values=values
            )
            activity = self.activity_schedule(
                activity_type, summary="Invoice rejected by Paynet", note=message
            )
        # error_log = values.get("error_detail")
        # if not error_log:
        #     error_log = _("An error of type {} occured.").format(
        #         values.get("error_type")
        #     )
        # activity.note += "<div class='mt16'><p>{}</p></div>".format(error_log)
