# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from string import Template

from freezegun import freeze_time

from odoo.tools import file_open

from ...ebill_paynet.tests.common import CommonCase


@freeze_time("2019-06-21 09:06:00")
class TestEbillPaynetCustomerFreeRef(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.invoice.name = "INV_TEST_01"
        cls.sale.customer_order_number = "888"
        cls.sale.customer_order_free_ref = "FREE"

    def test_invoice(self):
        """ Check XML payload genetated for an invoice."""
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
            file_open(
                "ebill_paynet_customer_free_ref/tests/examples/invoice_b2b.xml"
            ).read()
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
