# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from string import Template

from freezegun import freeze_time

from odoo import release
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import file_open

from .common import (
    BILLER_ID,
    EBILL_ACCOUNT_ID,
    CommonCase,
    clean_xml,
    compare_xml_line_by_line,
    drop_appendix_document,
)

TRANSACTION_ID = "190621090600-INVTEST01"


@tagged("post_install", "-at_install")
@freeze_time("2019-06-21 09:06:00")
class TestYellowbill(CommonCase):
    def _assert_payload(self, expected_sample):
        """Build the payload of the invoice and compare it to a sample."""
        self.invoice.name = "INV_TEST_01"
        payload = self.builder._export_invoice(
            self.invoice,
            biller_id=BILLER_ID,
            ebill_account_id=EBILL_ACCOUNT_ID,
            transaction_id=TRANSACTION_ID,
        )
        self.builder._validate_payload(payload)
        expected = Template(file_open(expected_sample).read()).substitute(
            TRANSACTION_ID=TRANSACTION_ID,
            CUSTOMER_ID=self.customer.id,
            SOFTWARE_VERSION=release.major_version,
        )
        self.assertFalse(
            compare_xml_line_by_line(
                clean_xml(drop_appendix_document(payload)),
                clean_xml(expected),
            )
        )

    def test_invoice(self):
        """The payload of an invoice paid by QR-IBAN.

        Scenario:
            1. Invoice a confirmed order to a customer, with a payment term.
            2. Build the YellowBill payload.
        Expected:
            - The payload is valid against the YellowBill schema.
            - It matches the expected document, sent as a bill with the
              company's QR-IBAN as the payment information.
        """
        self.invoice.invoice_payment_term_id = self.payment_term
        self._assert_payload(
            "account_invoice_export_yellowbill/tests/samples/invoice_qr_yb.xml"
        )

    def test_invoice_early_discount(self):
        """A payment term granting an early discount is reported in the summary.

        Scenario:
            1. Set a payment term granting 2% when paid within 10 days.
            2. Build the YellowBill payload.
        Expected:
            - The summary reports a discount of 2% for 10 days.
        """
        self.invoice.invoice_payment_term_id = self.env["account.payment.term"].create(
            {
                "name": "Skonto",
                "early_discount": True,
                "discount_days": 10,
                "discount_percentage": 2.0,
            }
        )
        self.invoice.invoice_date_due = "2019-08-20"
        self._assert_payload(
            "account_invoice_export_yellowbill/tests/samples/invoice_qr_yb_discount.xml"
        )

    def test_credit_note(self):
        """The payload of a credit note.

        Scenario:
            1. Turn the invoice into a posted credit note.
            2. Build the YellowBill payload as a credit.
        Expected:
            - The document is a credit advice, with no payment information,
              without the caller having to say it is a credit.
            - Every amount of the summary is negated.
        """
        self.invoice.name = "INV_TEST_01"
        self.invoice.invoice_date_due = "2019-07-01"
        self.invoice.move_type = "out_refund"
        self.invoice.action_post()
        self._assert_payload(
            "account_invoice_export_yellowbill/tests/samples/credit_note_yb.xml"
        )

    def test_payload_not_a_customer_invoice(self):
        """Only customer invoices and credit notes can be exported."""
        bill = self.env["account.move"].create(
            {"move_type": "in_invoice", "partner_id": self.customer.id}
        )
        with self.assertRaisesRegex(UserError, "not a customer invoice"):
            self.builder._export_invoice(
                bill,
                biller_id=BILLER_ID,
                ebill_account_id=EBILL_ACCOUNT_ID,
                transaction_id=TRANSACTION_ID,
            )

    def test_validate_payload_invalid(self):
        """A payload that does not match the schema is rejected."""
        with self.assertRaises(UserError):
            self.builder._validate_payload("<Envelope><Body /></Envelope>")
