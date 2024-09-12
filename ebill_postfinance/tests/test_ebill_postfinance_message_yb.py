# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
from string import Template

from freezegun import freeze_time
from lxml import etree as ET

from odoo.modules.module import get_module_root
from odoo.tools import file_open

from .common import CommonCase


@freeze_time("2019-06-21 09:06:00")
class TestEbillPostfinanceMessageYB(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schema_file = (
            get_module_root(os.path.dirname(__file__))
            + "/messages/ybInvoice_V2.0.4.xsd"
        )

    def test_invoice_qr(self):
        """Check XML payload genetated for an invoice."""
        # If ebill_postfinance_stock is installed it will break the test
        try:
            self.invoice.invoice_line_ids.sale_line_ids.write({"move_ids": False})
        except Exception:
            pass
        self.invoice.name = "INV_TEST_01"
        self.invoice.invoice_date_due = "2019-07-01"
        message = self.invoice.create_postfinance_ebill()
        message.set_transaction_id()
        message.payload = message._generate_payload_yb()
        # Validate the xml generated on top of the xsd schema
        node = ET.fromstring(message.payload.encode("utf-8"))
        self.assertXmlValidXSchema(node, xschema=None, filename=self.schema_file)
        # Remove the PDF file data from the XML to ease diff check
        lines = message.payload.splitlines()
        for pos, line in enumerate(lines):
            if line.find("MimeType") != -1:
                lines.pop(pos)
                break
        payload = "\n".join(lines).encode("utf8")
        # Prepare the XML file that is expected
        expected_tmpl = Template(
            file_open("ebill_postfinance/tests/examples/invoice_qr_yb.xml").read()
        )
        expected = expected_tmpl.substitute(
            TRANSACTION_ID=message.transaction_id, CUSTOMER_ID=self.customer.id
        ).encode("utf8")
        # Remove the comments in the expected xml
        expected_nocomment = [
            line
            for line in expected.split(b"\n")
            if not line.lstrip().startswith(b"<!--")
        ]
        expected_nocomment = b"\n".join(expected_nocomment)
        self.assertFalse(self.compare_xml_line_by_line(payload, expected_nocomment))
