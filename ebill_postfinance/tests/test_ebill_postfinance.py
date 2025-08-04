# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os

from odoo.tools import mute_logger

from .common import CommonCase, recorder

LOGGER = "odoo.addons.ebill_postfinance.models.ebill_postfinance_service"


class TestEbillPostfinance(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.transaction_id = "test-transaction-123"
        cls.invoice_message = cls.invoice.create_postfinance_ebill()

    @mute_logger("vcr.cassette", LOGGER)
    @recorder.use_cassette
    def test_ping_service(self):
        """Check the ping service testing purpose only."""
        self.service.ping_service()

    @mute_logger("vcr.cassette", LOGGER)
    @recorder.use_cassette
    def test_upload_file(self):
        """Check uploading an XML invoice to the service."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "samples", "yellowbill_qr_iban.xml"
            ),
        ) as f:
            data = f.read()
        data = data.encode("utf-8")
        res = self.service.upload_file(self.transaction_id, "XML", data)
        result = res[0]
        self.assertEqual(result.FileType, "XML")
        self.assertEqual(result.TransactionID, "test-transaction-123")
        self.assertEqual(result.ProcessingState, "OK")

    @mute_logger("vcr.cassette", LOGGER)
    @recorder.use_cassette
    def test_search_invoices(self):
        """Check the search invoice endpoint.

        Get the state of the invoice send in the previous test.
        And update the invoice message record with the result.

        """
        res = self.service.search_invoice(transaction_id=self.transaction_id)
        data = res.InvoiceList["SearchInvoice"][0]
        self.invoice_message.update_message_from_server_data(data)
        self.assertEqual(self.invoice_message.state, "error")
        self.assertEqual(self.invoice_message.server_state, "invalid")
