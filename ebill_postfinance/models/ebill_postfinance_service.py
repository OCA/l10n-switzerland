# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import logging.config

from ebilling_postfinance import ebilling_postfinance

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EbillPostfinanceService(models.Model):
    _name = "ebill.postfinance.service"
    _description = "Postfinance eBill service configuration"

    name = fields.Char(required=True)
    username = fields.Char()
    password = fields.Char()
    biller_id = fields.Char(string="Biller ID", size=17, required=True)
    use_test_service = fields.Boolean(string="Testing", help="Target the test service")
    partner_bank_id = fields.Many2one(
        comodel_name="res.partner.bank", string="Bank account", ondelete="restrict"
    )
    invoice_message_ids = fields.One2many(
        comodel_name="ebill.postfinance.invoice.message",
        inverse_name="service_id",
        string="Invoice Messages",
        readonly=True,
    )
    ebill_payment_contract_ids = fields.One2many(
        comodel_name="ebill.payment.contract",
        inverse_name="postfinance_service_id",
        string="Contracts",
        readonly=True,
    )
    active = fields.Boolean(default=True)
    file_type_to_use = fields.Selection(
        string="Invoice Format",
        default="XML",
        required=True,
        selection=[
            ("XML", "XML Yellow Bill"),
            ("EAI.XML", "Custom XML (SAPiDoc)"),
            # ("eai.edi", "Custom EDIFACT"),
            ("struct.pdf", "Factur X"),
        ],
    )
    use_file_type_xml_paynet = fields.Boolean(
        string="Use Paynet/SIX format",
        help="Enable use of legacy SIX/Paynet invoice format.",
    )
    operation_timeout = fields.Integer(
        string="HTTP Timeout",
        default="600",
        help="Timeout for each HTTP (GET, POST) request in seconds.",
    )

    def _get_service(self):
        return ebilling_postfinance.WebService(
            self.use_test_service,
            self.username,
            self.password,
            self.biller_id,
            self.operation_timeout,
        )

    def test_ping(self):
        """Test the service from the UI."""
        self.ensure_one()
        msg = ["Test connection to service"]
        res = self.ping_service()
        if res:
            msg.append(f"Success pinging service \n  Receive :{res}")
        else:
            msg.append(" - Failed pinging service")
        raise UserError("\n".join(msg))

    def ping_service(self, test_error=False, test_exception=False):
        """Ping the service, uses the authentication.

        test_error: will create an unhandled error in the repsonse
        test_exception: will create a FaultException

        """
        service = self._get_service()
        return service.ping()

    def search_invoice(self, transaction_id=None):
        """Get invoice status from the server.

        transaction_id:
        """
        service = self._get_service()
        res = service.search_invoices(transaction_id)
        if res.InvoiceCount == 0:
            _logger.info("Search invoice returned no invoice")
            return res
        if res.InvoiceCount < res.TotalInvoiceCount:
            # TODO handle the case where there is more to download ?
            _logger.info("Search invoice has more to download")
        for message in res.InvoiceList.SearchInvoice:
            _logger.info(f"Found record for message {message}")
            record = self.invoice_message_ids.search(
                [("transaction_id", "=", message.TransactionId)],
                limit=1,
                order="create_date desc",
            )
            if record:
                record.update_message_from_server_data(message)
            else:
                _logger.warning(f"Could not find record for message {message}")
        return res

    def upload_file(self, transaction_id, file_type, data):
        service = self._get_service()
        res = service.upload_files(transaction_id, file_type, data)
        return res

    def get_invoice_list(self, archive_data=False):
        service = self._get_service()
        res = service.get_invoice_list(archive_data)
        return res

    def get_process_protocol_list(self, archive_data=False):
        # Is this the processing result of an invoice ?
        service = self._get_service()
        res = service.get_process_protocol_list(archive_data)
        return res

    def get_ebill_recipient_subscription_status(self, recipient_id):
        service = self._get_service()
        res = service.get_ebill_recipient_subscription_status(recipient_id)
        return res

    def get_registration_protocol_list(self, archive_data=False):
        service = self._get_service()
        res = service.get_registration_protocol_list(archive_data)
        for registration_protocol in res or {}:
            self.get_registration_protocol(registration_protocol.CreateDate)
        return res

    def get_registration_protocol(self, create_date, archive_data=False):
        service = self._get_service()
        res = service.get_registration_protocol(create_date, archive_data)
        return res

    @api.model
    def cron_update_invoices(self):
        services = self.search([])
        for service in services:
            service.search_invoice()
