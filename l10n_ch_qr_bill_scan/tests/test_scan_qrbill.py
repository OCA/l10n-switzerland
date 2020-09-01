# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp (http://www.camptocamp.com/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import tools
from odoo.exceptions import UserError
from odoo.modules.module import get_resource_path
from odoo.tests import common

from ..tools import QR

# QR Reference
QRR = "210000000003139471430009017"

# Creditor Reference
CF = "RF18539007547034"

CH_IBAN = "CH15 3881 5158 3845 3843 7"
QR_IBAN = "CH21 3080 8001 2345 6782 7"


SCAN_DATA = [
    "SPC",
    "0200",
    "1",
    CH_IBAN.replace(" ", ""),
    "S",
    "Camptocamp",
    "EPFL Innovation Park",
    "Bldg A",
    "1015",
    "Lausanne",
    "CH",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "1949.75",
    "CHF",
    "S",
    "Your company",
    "Bahnhofplatz",
    "10",
    "3011",
    "Bern",
    "CH",
    "{ref_type}",
    "{ref}",
    "Instruction of 15.09.2019",
    "EPD",
    "",
    "",
    "",
]


class TestScanQRBill(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestScanQRBill, cls).setUpClass()
        cls.env.user.company_id.invoice_import_create_bank_account = True
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "Camptocamp",
                "street": "EPFL Innovation Park",
                "street2": "Bldg A",
                "zip": "1015",
                "city": "Lausanne",
                "country_id": cls.env.ref("base.ch").id,
                "supplier": True,
            }
        )

        cls.expense_account = cls.env["account.account"].create(
            {
                "code": "612AII",
                "name": "expense account invoice import",
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
            }
        )
        cls.env["account.invoice.import.config"].create(
            {
                "name": "Camptocamp - one line no product",
                "partner_id": cls.supplier.id,
                "invoice_line_method": "1line_no_product",
                "account_id": cls.expense_account.id,
            }
        )

    def wiz_import_invoice_file(self, file_path, file_name):
        """ Import a file of a vendor bill """
        with tools.file_open(file_path, "rb") as f:
            invoice_file = base64.b64encode(f.read())
        wiz = self.env["account.invoice.import"].create({})
        wiz.invoice_file = invoice_file
        wiz.invoice_filename = file_name
        return wiz

    def import_invoice_file(self, file_path, file_name):
        """ Import scanned data from a vendor bill

        And return the created invoice
        """
        wiz = self.wiz_import_invoice_file(file_path, file_name)
        res = wiz.import_invoice()
        if res.get("res_model") == "account.invoice":
            invoice = self.env["account.invoice"].browse(res["res_id"])
            return invoice
        return None

    def wiz_import_invoice_scan(self, invoice_scan):
        """ Import scanned data from a vendor bill """
        wiz = self.env["account.invoice.import"].create({})
        wiz.invoice_scan = invoice_scan
        return wiz

    def import_invoice_scan(self, invoice_scan):
        """ Import scanned data from a vendor bill

        And return the created invoice
        """
        wiz = self.wiz_import_invoice_scan(invoice_scan)
        res = wiz.import_invoice()
        if res.get("res_model") == "account.invoice":
            invoice = self.env["account.invoice"].browse(res["res_id"])
            return invoice
        return None

    def test_scan_QR_free_ref(self):
        scan_data = SCAN_DATA[:]
        scan_data = "\n".join(scan_data).format(ref_type="NON", ref="")
        invoice = self.import_invoice_scan(scan_data)

        self.assertEqual(invoice.partner_id, self.supplier)
        self.assertFalse(invoice.reference)
        self.assertEqual(invoice.state, "draft")
        iban = invoice.partner_bank_id.acc_number
        self.assertEqual(iban, CH_IBAN.replace(' ', ''))
        self.assertEqual(invoice.amount_total, 1949.75)

    def test_scan_QR_QRR(self):
        scan_data = SCAN_DATA[:]
        scan_data[QR.IBAN] = QR_IBAN.replace(" ", "")
        scan_data = "\n".join(scan_data).format(ref_type="QRR", ref=QRR)
        invoice = self.import_invoice_scan(scan_data)

        self.assertEqual(invoice.partner_id, self.supplier)
        self.assertEqual(invoice.reference, QRR)
        self.assertEqual(invoice.state, "draft")
        iban = invoice.partner_bank_id.acc_number
        self.assertEqual(iban, QR_IBAN.replace(" ",""))
        self.assertEqual(invoice.amount_total, 1949.75)

    def test_scan_QR_CF(self):
        scan_data = SCAN_DATA[:]
        scan_data = "\n".join(scan_data).format(ref_type="SCOR", ref=CF)
        invoice = self.import_invoice_scan(scan_data)

        self.assertEqual(invoice.partner_id, self.supplier)
        self.assertEqual(invoice.reference, CF)
        self.assertEqual(invoice.state, "draft")
        iban = invoice.partner_bank_id.acc_number
        self.assertEqual(iban, CH_IBAN.replace(' ', ''))
        self.assertEqual(invoice.amount_total, 1949.75)

    def test_scan_QR_new_partner(self):
        scan_data = SCAN_DATA
        scan_data[QR.CREDITOR_NAME] = "New Vendor"
        scan_data = "\n".join(scan_data).format(ref_type="NON", ref="")
        wiz = self.wiz_import_invoice_scan(scan_data)
        wiz.import_invoice()

        self.assertEqual(wiz.state, "select-partner")
        self.assertEqual(wiz.partner_name, "New Vendor")
        self.assertEqual(wiz.partner_street, "EPFL Innovation Park Bldg A")
        self.assertEqual(wiz.partner_zip, "1015")
        self.assertEqual(wiz.partner_city, "Lausanne")
        self.assertEqual(wiz.partner_country_id, self.env.ref("base.ch"))

    def test_scan_QR_swico(self):
        pass
        # Not implemented
        # self.assertTrue(False)

    def test_scan_QR_wrong_swico(self):
        pass
        # Not implemented
        # self.assertTrue(False)

    def test_scan_QR_extra_first_lines(self):
        scan_data = ["", ""] + SCAN_DATA[:]
        scan_data = "\n".join(scan_data).format(ref_type="NON", ref="")

        invoice = self.import_invoice_scan(scan_data)
        self.assertEqual(invoice.partner_id, self.supplier)
        self.assertFalse(invoice.reference)
        self.assertEqual(invoice.state, "draft")
        iban = invoice.partner_bank_id.acc_number
        self.assertEqual(iban, CH_IBAN.replace(' ', ''))
        self.assertEqual(invoice.amount_total, 1949.75)

    def test_scan_QR_missing_lines(self):
        scan_data = SCAN_DATA[:-10]
        scan_data = "\n".join(scan_data).format(ref_type="NON", ref="")

        with self.assertRaises(UserError):
            self.import_invoice_scan(scan_data)

    def test_scan_QR_wrong_size(self):
        scan_data = SCAN_DATA[:15] + SCAN_DATA[20:]
        scan_data = "\n".join(scan_data).format(ref_type="NON", ref="")

        with self.assertRaises(UserError):
            self.import_invoice_scan(scan_data)

    def test_scan_QR_gibberish(self):
        scan_data = "saoeutheSPCoauhoess" + "\n" * 30

        with self.assertRaises(UserError):
            self.import_invoice_scan(scan_data)

    def test_scan_QR_bad_amount(self):
        scan_data = SCAN_DATA[:]
        scan_data[QR.AMOUNT] = "not a number"
        scan_data = "\n".join(scan_data).format(ref_type="NON", ref="")

        with self.assertRaises(UserError):
            self.import_invoice_scan(scan_data)

    def test_import_QR_pdf(self):
        partner = self.env["res.partner"].create(
            {
                "name": "My Company",  # this was generated from Odoo
                "street": "addr 1",
                "street2": "",
                "zip": "2074",
                "city": "Marin",
                "country_id": self.env.ref("base.ch").id,
                "supplier": True,
            }
        )
        self.env["account.invoice.import.config"].create(
            {
                "name": "Camptocamp - one line no product",
                "partner_id": partner.id,
                "invoice_line_method": "1line_no_product",
                "account_id": self.expense_account.id,
            }
        )

        invoice_fp = get_resource_path(
            "l10n_ch_qr_bill_scan", "tests", "data", "qr-bill.pdf"
        )
        invoice = self.import_invoice_file(invoice_fp, "qr-bill.pdf")
        self.assertTrue(invoice)
        self.assertEqual(invoice.reference, "000000000000000000202000058")
        self.assertEqual(invoice.amount_total, 1.0)
