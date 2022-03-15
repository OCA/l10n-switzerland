# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from string import Template

import mock
from freezegun import freeze_time

from odoo.tools import file_open

from .common import CommonCase

EBILL = "odoo.addons.ebill_paynet.models.paynet_invoice_message.PaynetInvoiceMessage."


@freeze_time("2019-06-21 09:06:00")
class TestInvoiceMessage(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_invoice_qr(self):
        """Check XML payload genetated for an invoice."""
        self.invoice.name = "INV_TEST_01"
        self.invoice.invoice_date_due = "2019-07-01"
        message = self.invoice.create_paynet_message()
        message.payload = message._generate_payload()
        # Remove the PDF file data from the XML to ease testing
        lines = message.payload.splitlines()
        for pos, line in enumerate(lines):
            if line.find("Back-Pack") != -1:
                lines.pop(pos)
                break
        payload = "\n".join(lines).encode("utf8")
        self.assertXmlDocument(payload)
        # Prepare the XML file that is expected
        expected_tmpl = Template(
            file_open("ebill_paynet/tests/examples/invoice_qr_b2b.xml").read()
        )
        expected = expected_tmpl.substitute(IC_REF=message.ic_ref).encode("utf8")
        # Remove the comments in the expected xml
        expected_nocomment = [
            line
            for line in expected.split(b"\n")
            if not line.lstrip().startswith(b"<!--")
        ]
        expected_nocomment = b"\n".join(expected_nocomment)
        self.assertFalse(self.compare_xml_line_by_line(payload, expected_nocomment))
        self.assertXmlEquivalentOutputs(payload, expected_nocomment)

    def test_invoice_esr(self):
        """Check XML payload genetated for an invoice."""
        self.contract.payment_type = "isr"
        self.invoice.name = "INV_TEST_01"
        self.invoice.invoice_date_due = "2019-07-01"
        message = self.invoice.create_paynet_message()
        message.payload = message._generate_payload()
        # Remove the PDF file data from the XML to ease testing
        lines = message.payload.splitlines()
        for pos, line in enumerate(lines):
            if line.find("Back-Pack") != -1:
                lines.pop(pos)
                break
        payload = "\n".join(lines).encode("utf8")
        self.assertXmlDocument(payload)
        # Prepare the XML file that is expected
        expected_tmpl = Template(
            file_open("ebill_paynet/tests/examples/invoice_isr_b2b.xml").read()
        )
        expected = expected_tmpl.substitute(IC_REF=message.ic_ref).encode("utf8")
        # Remove the comments in the expected xml
        expected_nocomment = [
            line
            for line in expected.split(b"\n")
            if not line.lstrip().startswith(b"<!--")
        ]
        expected_nocomment = b"\n".join(expected_nocomment)
        self.assertFalse(self.compare_xml_line_by_line(payload, expected_nocomment))
        self.assertXmlEquivalentOutputs(payload, expected_nocomment)

    @mock.patch(EBILL + "_get_ic_ref")
    def test_invoice_qr_rounding(self, get_ic_ref):
        """Test case to check float rounding fits well."""
        get_ic_ref.return_value = "SA000000000003"
        invoice = self.env["account.move"].create(
            {
                "name": "INV_TEST_01",
                "partner_id": self.customer.id,
                "invoice_date_due": "2019-07-01",
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (0, 0, {"name": "A little note", "display_type": "line_note"}),
                    (
                        0,
                        0,
                        {
                            "name": "Phone support",
                            "quantity": 1.0,
                            "price_unit": 4.5,
                            "account_id": self.at_receivable.id,
                            "tax_ids": [(4, self.tax7.id, 0)],
                        },
                    ),
                ],
            }
        )
        invoice.action_post()
        invoice.payment_reference = "1234567890"
        invoice.partner_bank_id = self.partner_bank.id
        # amount inside is not rounded
        self.assertEqual(invoice.amount_by_group[0][1], 0.35000000000000003)
        message = invoice.create_paynet_message()
        message.payload = message._generate_payload()
        # Remove the PDF file data from the XML to ease testing
        lines = message.payload.splitlines()
        for pos, line in enumerate(lines):
            if line.find("Back-Pack") != -1:
                lines.pop(pos)
                break
        payload = "\n".join(lines).encode("utf8")
        self.assertXmlDocument(payload)
        # Prepare the XML file that is expected
        expected_tmpl = Template(
            file_open("ebill_paynet/tests/examples/invoice_qr_b2b_rounded.xml").read()
        )
        expected = expected_tmpl.substitute(IC_REF=message.ic_ref).encode("utf8")
        # Remove the comments in the expected xml
        expected_nocomment = [
            line
            for line in expected.split(b"\n")
            if not line.lstrip().startswith(b"<!--")
        ]
        expected_nocomment = b"\n".join(expected_nocomment)
        self.assertFalse(self.compare_xml_line_by_line(payload, expected_nocomment))
        self.assertXmlEquivalentOutputs(payload, expected_nocomment)
