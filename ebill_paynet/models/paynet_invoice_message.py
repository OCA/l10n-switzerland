# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
from datetime import datetime

# Needs Jinja 2.10
from jinja2 import Environment, FileSystemLoader, select_autoescape
from zeep.exceptions import Fault

from odoo import fields, models
from odoo.modules.module import get_module_root

from odoo.addons.base.models.res_bank import sanitize_account_number

from ..components.api import PayNetDWS

MODULE_PATH = get_module_root(os.path.dirname(__file__))
INVOICE_TEMPLATE_2013 = "invoice-2013A.xml"
INVOICE_TEMPLATE_2003 = "invoice-2003A.xml"
TEMPLATE_DIR = MODULE_PATH + "/messages"

DOCUMENT_TYPE = {"out_invoice": "EFD", "out_refund": "EGS"}

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["xml"]),
)
template_2013 = jinja_env.get_template(INVOICE_TEMPLATE_2013)
template_2003 = jinja_env.get_template(INVOICE_TEMPLATE_2003)


class PaynetInvoiceMessage(models.Model):
    _name = "paynet.invoice.message"
    _description = "Paynet shipment send to service"

    service_id = fields.Many2one(
        comodel_name="paynet.service",
        string="Paynet Service",
        required=True,
        ondelete="restrict",
        readonly=True,
    )
    invoice_id = fields.Many2one(comodel_name="account.move", ondelete="restrict")
    attachment_id = fields.Many2one("ir.attachment", "PDF")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("done", "Done"),
            ("reject", "Reject"),
            ("error", "Error"),
        ],
        default="draft",
    )
    ic_ref = fields.Char(
        string="IC Ref", size=14, help="Document interchange reference"
    )
    # Set with invoice_id.number but also with returned data from server ?
    ref = fields.Char("Reference N°", size=35)
    ebill_account_number = fields.Char("Paynet Id", size=20)
    payload = fields.Text("Payload sent")
    response = fields.Text("Response recieved")
    shipment_id = fields.Char(size=24, help="Shipment Id on Paynet service")
    payment_type = fields.Selection(
        selection=[("qr", "QR"), ("esr", "ESR"), ("esp", "ESP"), ("npy", "NPY")],
        default="qr",
        readonly=True,
    )

    def _get_ic_ref(self):
        return "SA%012d" % self.id

    def send_to_paynet(self):
        for message in self:
            message.payload = message._generate_payload()
            try:
                shipment_id = message.service_id.take_shipment(message.payload)
                message.shipment_id = shipment_id
                message.state = "sent"
            except Fault as e:
                message.response = PayNetDWS.handle_fault(e)
                message.state = "error"

    @staticmethod
    def format_date(date_string=None):
        if not date_string:
            date_string = datetime.now()
        return date_string.strftime("%Y%m%d")

    def _generate_payload(self):
        self.ensure_one()
        assert self.state == "draft"
        self.ic_ref = self._get_ic_ref()
        bank_account = ""
        if self.payment_type == "qr":
            bank_account = sanitize_account_number(
                self.invoice_id.invoice_partner_bank_id.l10n_ch_qr_iban
                or self.invoice_id.invoice_partner_bank_id.acc_number
            )
        else:
            bank_account = (
                self.invoice_id.invoice_partner_bank_id.l10n_ch_isr_subscription_chf
            )
            if bank_account:
                account_parts = bank_account.split("-")
                bank_account = (
                    account_parts[0] + account_parts[1].rjust(6, "0") + account_parts[2]
                )
            else:
                bank_account = ""

        params = {
            "client_pid": self.service_id.client_pid,
            "invoice": self.invoice_id,
            "invoice_line": self.invoice_id.paynet_invoice_line_ids(),
            "biller": self.invoice_id.company_id,
            "customer": self.invoice_id.partner_id,
            "delivery": self.invoice_id.partner_shipping_id,
            "pdf_data": self.attachment_id.datas.decode("ascii"),
            "bank": self.invoice_id.invoice_partner_bank_id,
            "bank_account": bank_account,
            "ic_ref": self.ic_ref,
            "payment_type": self.payment_type,
            "document_type": DOCUMENT_TYPE[self.invoice_id.type],
            "format_date": self.format_date,
            "ebill_account_number": self.ebill_account_number,
        }
        amount_by_group = []
        # Get the percentage of the tax from the name of the group
        # Could be improve by searching in the account_tax linked to the group
        for taxgroup in self.invoice_id.amount_by_group:
            rate = taxgroup[0].split()[-1:][0][:-1]
            amount_by_group.append((rate or "0", taxgroup[1], taxgroup[2],))
        params["amount_by_group"] = amount_by_group

        if self.service_id.service_type == "b2b":
            payload = template_2003.render(params)
        else:
            payload = template_2013.render(params)
        return payload

    def update_invoice_status(self):
        """Update the export status in the chatter."""
        for message in self:
            if message.state == "done":
                message.invoice_id.log_invoice_accepted_by_system()
            elif message.state in ["reject", "error"]:
                message.invoice_id.log_invoice_refused_by_system()
