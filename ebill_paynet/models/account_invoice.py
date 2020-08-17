# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = "account.move"

    @api.onchange("transmit_method_id", "partner_id")
    def _onchange_transmit_method_id(self):
        if self.type not in ("out_invoice", "out_refund"):
            return
        paynet_method = self.env.ref("ebill_paynet.paynet_transmit_method")
        if self.transmit_method_id == paynet_method:
            # It is not called when selecting the customer ?
            contract = self.get_active_contract(
                self.partner_id, self.transmit_method_id
            )
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
        return "Paynet invoice generated and in state {}".format(message.state)

    # TODO: Should go in base_ebill_payment_contract
    @api.model
    def get_active_contract(self, partner, transmit_method):
        # FIXME: Search on non stored field
        contract = self.env["ebill.payment.contract"].search(
            [("is_valid", "=", True), ("partner_id", "=", partner.id)], limit=1,
        )
        if not contract:
            _logger.error(
                "Paynet contract for {} not found for {}".format(
                    partner.name, transmit_method.name
                )
            )
        return contract

    def create_paynet_message(self):
        """Generate the paynet message for an invoice."""
        self.ensure_one()
        contract = self.get_active_contract(self.partner_id, self.transmit_method_id)
        if not contract:
            return
        r = self.env["ir.actions.report"]._get_report_from_name(
            "account.report_invoice"
        )
        pdf, _ = r.render([self.id])
        message = self.env["paynet.invoice.message"].create(
            {
                "service_id": contract.paynet_service_id.id,
                "invoice_id": self.id,
                "ebill_account_number": contract.paynet_account_number,
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

    def log_invoice_accepted_by_system(self):
        """ """
        self.activity_feedback(
            ["ebill_paynet.mail_activity_dws_error"],
            feedback="It worked on a later try",
        )
        self.message_post(body=_("Invoice accepted by the Paynet system"))

    def log_invoice_refused_by_system(self):
        """ """
        activity_type = "ebill_paynet.mail_activity_dws_error"
        activity = self.activity_reschedule(
            [activity_type], date_deadline=fields.Date.today()
        )
        values = {}
        if not activity:
            message = self.env.ref("ebill_paynet.dws_reject_invoice").render(
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

    def _is_isr_ref(self, ref):
        return False
