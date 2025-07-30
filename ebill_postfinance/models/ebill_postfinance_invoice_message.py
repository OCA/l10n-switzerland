# Copyright 2019-2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
from datetime import datetime

import pytz
from jinja2 import Environment, FileSystemLoader
from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.modules.module import get_module_root

from odoo.addons.base.models.res_bank import sanitize_account_number

_logger = logging.getLogger(__name__)

MODULE_PATH = get_module_root(os.path.dirname(__file__))
INVOICE_TEMPLATE_2003 = "invoice-2003A.jinja"
INVOICE_TEMPLATE_YB = "invoice-yellowbill.jinja"
TEMPLATE_DIR = [MODULE_PATH + "/messages"]
XML_SCHEMA_YB = MODULE_PATH + "/messages/ybInvoice_V2.0.4.xsd"

DOCUMENT_TYPE = {"out_invoice": "EFD", "out_refund": "EGS"}


class EbillPostfinanceInvoiceMessage(models.Model):
    _name = "ebill.postfinance.invoice.message"
    _description = "Postfinance message send to service"

    service_id = fields.Many2one(
        comodel_name="ebill.postfinance.service",
        string="Service used",
        required=True,
        ondelete="restrict",
        readonly=True,
    )
    ebill_payment_contract_id = fields.Many2one(comodel_name="ebill.payment.contract")
    invoice_id = fields.Many2one(comodel_name="account.move", ondelete="restrict")
    transaction_id = fields.Char()
    file_type_used = fields.Char()
    submitted_on = fields.Datetime(string="Submitted on")
    attachment_id = fields.Many2one("ir.attachment", "PDF")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("error", "Error"),
            ("processing", "Processing"),
            ("reject", "Reject"),
            ("done", "Done"),
        ],
        default="draft",
    )
    server_state = fields.Selection(
        selection=[
            ("invalid", "Invalid"),
            ("processing", "Processing"),
            ("unsigned", "Unsigned"),
            ("open", "Open"),
            ("paid", "Paid"),
            # Not encountered states
            ("rejected", "Rejected"),
            ("incomplete", "Incomplete"),
            ("deleted", "Deleted"),
        ],
    )
    server_reason_code = fields.Integer(string="Error code")
    server_reason_text = fields.Char(string="Error text")

    # Set with invoice_id.number but also with returned data from server ?
    ref = fields.Char("Reference No.", size=35)
    ebill_account_number = fields.Char("Payer Id", size=20)
    payload = fields.Text("Payload sent")
    payload_size = fields.Float("Payload Size (MB)", digits=(6, 3), readonly=True)
    response = fields.Text()
    payment_type = fields.Selection(
        selection=[
            ("iban", "IBAN"),
            ("credit", "CREDIT"),
            ("other", "OTHER"),
            ("dd", "DD"),
            ("esr", "ESR"),
        ],
        default="iban",
        readonly=True,
    )

    @api.model
    def _get_payload_size(self, payload):
        size_in_bytes = len(payload)
        if size_in_bytes > 0:
            size_in_bytes = size_in_bytes / 1000000
        return size_in_bytes

    def set_transaction_id(self):
        self.ensure_one()
        self.transaction_id = "-".join(
            [
                fields.Datetime.now().strftime("%y%m%d%H%M%S"),
                self.invoice_id.name.replace("/", "").replace("_", ""),
            ]
        )

    def update_message_from_server_data(self, data):
        """Update the invoice message with data received from the server.

        Keyword arguments:
        data -- Structure from the api
                Example:
                {
                    'BillerId': '41101000001021209',
                    'TransactionId': 'INV_2022_03_0001_2022_03_26_08_31_xml',
                    'eBillAccountId': '123412341234',
                    'Amount': Decimal('0'),
                    'State': 'Invalid',
                    'PaymentType': None,
                    'ESRReferenceNbr': None,
                    'DeliveryDate': datetime.datetime(2022, 3, 26, 0, 0),
                    'PaymentDueDate': None,
                    'ReasonCode': '16',
                    'ReasonText': 'some good reason'
                }
        """
        self.ensure_one()
        self.server_state = data.State.lower()
        self.server_reason_code = data.ReasonCode
        self.server_reason_text = data.ReasonText
        if self.server_state in ["invalid"]:
            self.state = "error"
        elif self.server_state == "processing":
            self.state = "processing"
        elif self.server_state == "paid":
            self.set_as_paid(data)

    def set_as_paid(self, data):
        for record in self:
            if record.state != "done":
                record.state = "done"
                record.invoice_id.message_post(
                    body=self.env._("Invoice paid through eBilling")
                )

    @api.model
    def _remove_pdf_data_from_payload(self, data):
        """Minimize payload size to be kept.

        Remove the node containing the pdf data from the xml.

        """
        start_node = "<Appendix>"
        end_node = "</Appendix>"
        start = data.find(start_node)
        if start < 0:
            return data
        end = data.find(end_node, start)
        return data[0:start] + data[end + len(end_node) :]

    def send_to_postfinance(self):
        # TODO: Could sent multiple with one call
        for message in self:
            message.file_type_used = message.service_id.file_type_to_use
            message.set_transaction_id()
            payload = message._generate_payload()
            data = payload.encode("utf-8")
            message.payload = self._remove_pdf_data_from_payload(payload)
            message.payload_size = self._get_payload_size(payload)
            try:
                # TODO: Handle file type from service configuation
                res = message.service_id.upload_file(
                    message.transaction_id, message.file_type_used, data
                )
                response = res[0]
                if response.ProcessingState == "OK":
                    message.state = "sent"
                    submit_date_utc = response.SubmitDate.astimezone(pytz.utc)
                    message.submitted_on = submit_date_utc.replace(tzinfo=None)
                    message.response = response
                else:
                    message.state = "error"
                    message.server_reason_code = "NOK"
                    message.server_reason_text = "Could not be sent to sftp"
            except Exception as ex:
                message.response = "Exception sending to Postfinance"
                message.state = "error"
                raise ex

    @staticmethod
    def format_date(date_string=None):
        """Format a date in the Jinja template."""
        if not date_string:
            date_string = datetime.now()
        return date_string.strftime("%Y%m%d")

    @staticmethod
    def format_date_yb(date_string=None):
        """Format a date in the Jinja template."""
        if not date_string:
            date_string = datetime.now()
        return date_string.strftime("%Y-%m-%d")

    def _get_payload_params(self):
        bank_account = ""
        bank_account = sanitize_account_number(
            self.invoice_id.partner_bank_id.l10n_ch_qr_iban
            or self.invoice_id.partner_bank_id.acc_number
            or ""
        )
        params = {
            "client_pid": self.service_id.biller_id,
            "invoice": self.invoice_id,
            "invoice_lines": self.invoice_id.postfinance_invoice_line_ids(),
            "biller": self.invoice_id.company_id,
            "customer": self.invoice_id.partner_id,
            "delivery": self.invoice_id.partner_shipping_id,
            "pdf_data": self.attachment_id.datas.decode("ascii"),
            "bank": self.invoice_id.partner_bank_id,
            "bank_account": bank_account,
            "transaction_id": self.transaction_id,
            "payment_type": self.payment_type,
            "document_type": DOCUMENT_TYPE[self.invoice_id.move_type],
            "format_date": self.format_date,
            "ebill_account_number": self.ebill_account_number,
            "discount_template": "",
            "discount": {},
        }
        amount_by_group = []
        # Get the percentage of the tax from the name of the group
        # Could be improve by searching in the account_tax linked to the group
        for taxgroup in self.invoice_id.amount_by_group:
            rate = taxgroup[0].split()[-1:][0][:-1]
            amount_by_group.append(
                (
                    rate or "0",
                    taxgroup[1],
                    taxgroup[2],
                )
            )
        params["amount_by_group"] = amount_by_group
        # Get the invoice due date
        date_due = self.format_date(
            self.invoice_id.invoice_date_due or self.invoice_id.invoice_date
        )
        params["date_due"] = date_due
        return params

    def _get_payload_params_yb(self):
        bank_account = sanitize_account_number(
            self.invoice_id.partner_bank_id.l10n_ch_qr_iban
            or self.invoice_id.partner_bank_id.acc_number
            or ""
        )
        delivery = (
            self.invoice_id.partner_shipping_id
            if self.invoice_id.partner_shipping_id != self.invoice_id.partner_id
            else False
        )
        orders = self.invoice_id.line_ids.sale_line_ids.mapped("order_id")
        params = {
            "invoice": self.invoice_id,
            "saleorder": orders,
            "message": self,
            "client_pid": self.service_id.biller_id,
            "invoice_lines": self.invoice_id.postfinance_invoice_line_ids(),
            "biller": self.invoice_id.company_id,
            "customer": self.invoice_id.partner_id,
            "delivery": delivery,
            "pdf_data": self.attachment_id.datas.decode("ascii"),
            "bank": self.invoice_id.partner_bank_id,
            "bank_account": bank_account,
            "transaction_id": self.transaction_id,
            "payment_type": self.payment_type,
            "amount_sign": -1 if self.payment_type == "credit" else 1,
            "document_type": DOCUMENT_TYPE[self.invoice_id.move_type],
            "format_date": self.format_date_yb,
            "ebill_account_number": self.ebill_account_number,
            "discount_template": "",
            "discount": {},
            "invoice_line_stock_template": "",
        }
        amount_by_group = []
        # Get the percentage of the tax from the name of the group
        # Could be improve by searching in the account_tax linked to the group
        for subtotal in self.invoice_id.tax_totals["subtotals"]:
            for taxgroup in subtotal["tax_groups"]:
                rate = taxgroup["group_name"].split()[-1:][0][:-1]
                amount_by_group.append(
                    (
                        rate or "0",
                        taxgroup["tax_amount"],
                        taxgroup["base_amount"],
                    )
                )
        params["amount_by_group"] = amount_by_group
        # Get the invoice due date
        date_due = self.format_date_yb(
            self.invoice_id.invoice_date_due or self.invoice_id.invoice_date
        )
        params["date_due"] = date_due
        return params

    def _get_jinja_env(self, template_dir):
        jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True,
        )
        # Force the truncate filter to be exact
        jinja_env.policies["truncate.leeway"] = 0
        return jinja_env

    def _get_template(self, jinja_env):
        return jinja_env.get_template(INVOICE_TEMPLATE_2003)

    def _get_template_yb(self, jinja_env):
        return jinja_env.get_template(INVOICE_TEMPLATE_YB)

    def _generate_payload(self):
        self.ensure_one()
        assert self.state in ("draft", "error")
        if self.service_id.file_type_to_use == "XML":
            if self.service_id.use_file_type_xml_paynet:
                return self._generate_payload_paynet()
            else:
                return self._generate_payload_yb()
        return

    def _generate_payload_paynet(self):
        """Generates the xml in the paynet format."""
        params = self._get_payload_params()
        jinja_env = self._get_jinja_env(TEMPLATE_DIR)
        jinja_template = self._get_template(jinja_env)
        return jinja_template.render(params)

    def _generate_payload_yb(self):
        """Generates the xml in the yellowbill format."""
        params = self._get_payload_params_yb()
        jinja_env = self._get_jinja_env(TEMPLATE_DIR)
        jinja_template = self._get_template_yb(jinja_env)
        return jinja_template.render(params)

    def validate_xml_payload(self):
        """Check the validity of yellowbill xml."""
        schema = etree.XMLSchema(file=XML_SCHEMA_YB)
        parser = etree.XMLParser(schema=schema)
        try:
            etree.fromstring(self.payload.encode("utf-8"), parser)
        except etree.XMLSyntaxError as ex:
            raise UserError(ex.error_log) from ex
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("The payload is valid."),
                "sticky": False,
            },
        }

    def update_invoice_status(self):
        """Update the export status in the chatter."""
        for message in self:
            if message.state == "done":
                message.invoice_id.log_invoice_accepted_by_system()
            elif message.state in ["reject", "error"]:
                message.invoice_id.log_invoice_refused_by_system()
