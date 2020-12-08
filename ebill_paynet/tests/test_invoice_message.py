# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from string import Template

from freezegun import freeze_time

from odoo.tools import file_open

from .common import CommonCase


@freeze_time("2019-06-07 09:06:00")
class TestInvoiceMessage(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_icref_generation(self):
        """ """
        message = self.invoice_1.create_paynet_message()
        message.ic_ref = message._get_ic_ref()
        self.assertEqual(message.ic_ref, "SA%012d" % message.id)

    def test_invoice(self):
        """ Check XML payload genetated for an invoice."""
        self.invoice_1.name = "INV_TEST_01"
        # self.invoice_1.action_invoice_sent()
        # TODO set a due date different to create date
        # self.invoice_1.date_due = '2019-07-01'
        self.invoice_1.state = "posted"
        message = self.invoice_1.create_paynet_message()
        message.payload = message._generate_payload()
        # Remove the PDF file data from the XML to ease testing
        lines = message.payload.splitlines()
        for pos, line in enumerate(lines):
            if line.find("Back-Pack") != -1:
                lines.pop(pos + 1)
                break
        payload = "\n".join(lines).encode("utf8")
        # self.assertXmlDocument(payload)
        # Prepare the XML file that is expected
        expected_tmpl = Template(
            file_open("ebill_paynet/tests/examples/invoice_1.xml").read()
        )
        expected = expected_tmpl.substitute(IC_REF=message.ic_ref).encode("utf8")
        self.assertFalse(self.compare_xml_line_by_line(payload, expected))
        self.assertXmlEquivalentOutputs(payload, expected)
