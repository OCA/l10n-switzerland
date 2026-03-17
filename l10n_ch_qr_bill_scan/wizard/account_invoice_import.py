# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.modules.module import get_resource_path

from ..tools import QR

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    import pdf2image
    from pyzbar.pyzbar import ZBarSymbol, decode
except ImportError:
    # Necessary libraries to decode QR from pdf are
    # not installed
    logger.warning(
        "Swiss QR detection in Vendor Bill pdf disabled."
        " To enable it, please install pyzbar, pdf2image, cv2 and numpy."
    )
    decode = False


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    invoice_scan = fields.Text(string="Scan of the invoice")

    def import_invoices(self):
        self.ensure_one()
        if self.invoice_scan:
            # handle Windows line endings
            invoice_scan = self.invoice_scan.replace("\r\n", "\n")
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "scan.qr",
                    "datas": base64.b64encode(invoice_scan.encode()),
                    "res_model": self._name,
                    "res_id": self.id,
                }
            )
            self.invoice_attachment_ids |= attachment
        return super().import_invoices()

    @api.model
    def _get_qr_address(self, address_lines):
        adr_type, name, adr_line1, adr_line2, zzip, city, country = address_lines
        address = {
            "name": name,
            "country_code": country,
        }
        if adr_type == "S":
            address["street"] = " ".join([adr_line1, adr_line2])
            address["zip"] = zzip
            address["city"] = city
        else:
            address["street"] = adr_line1
            address["zip"] = adr_line2.split(" ")[0]
            address["city"] = adr_line2.split(" ")[1]

        return address

    @api.model
    def _parse_billing_info(self, bill_info):
        # TODO not implemented
        return {}

    @api.model
    def parse_qrbill(self, qr_data):
        qr_match = QR.valid_re.search(qr_data)
        if not qr_match:
            raise UserError(_("The data doesn't match with a QR-Code from a QR-bill"))
        # Ignore everything before "SPC"
        if qr_match.start() > 0:
            qr_data = qr_data[qr_match.start() :]

        qr_data = qr_data.split("\n")

        try:
            amount = float(qr_data[QR.AMOUNT])
        except ValueError as exc:
            raise UserError(_("The {} ")) from exc
        parsed_inv = {
            "iban": qr_data[QR.IBAN],
            "partner": self._get_qr_address(
                qr_data[QR.CREDITOR : QR.CREDITOR + QR.ADR_LEN]
            ),
            "amount_total": amount,
            "currency": {"iso": qr_data[QR.CURRENCY]},
            "invoice_number": qr_data[QR.REF],
            "description": qr_data[QR.MSG],
        }
        # From the specs it's unclear if the return line is mandatory on EPD
        if len(qr_data) > QR.BILL_INFO:
            parsed_inv.update(self._parse_billing_info(qr_data[QR.BILL_INFO]))
        return parsed_inv

    @api.model
    def _read_swiss_qr_code(self, bill_img):
        # find the QR code using the Swiss Cross and crop around it to help
        # pyzbar to read it
        ch_cross_img = cv2.imread(
            get_resource_path("l10n_ch_qr_bill_scan", "data", "CH-Cross_7mm.png")
        )
        ch_cross_img = cv2.resize(ch_cross_img, (55, 55))
        res = cv2.matchTemplate(ch_cross_img, bill_img, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= 0.8)

        if not locations or locations[0].size == 0:
            raise UserError(_("QR-Code is not readable."))
        logger.debug("QR-Code swiss cross found")
        y = locations[0][0]
        x = locations[1][0]
        # zbar needs some help to find the QR in a whole page
        # the qrcode is approx 358 x 358 cropping at 375 x 375 to get some margin
        cropped_img = bill_img[y - 175 : y + 175 + 55, x - 175 : x + 175 + 55]
        data = decode(cropped_img, symbols=[ZBarSymbol.QRCODE])
        if not data:
            logger.debug("QR-Code is not readable, attempt to patch it")
            # As we found the swiss cross we assume there is a QR code to read
            # try to patch the QR by replacing the swiss cross
            patch_img = cv2.imread(
                get_resource_path("l10n_ch_qr_bill_scan", "data", "QR-patch.png")
            )
            bill_img[y : y + patch_img.shape[0], x : x + patch_img.shape[1]] = patch_img
            cropped_img = bill_img[y - 175 : y + 175 + 55, x - 175 : x + 175 + 55]
            data = decode(cropped_img, symbols=[ZBarSymbol.QRCODE])
        return data

    @api.model
    def parse_pdf_invoice(self, file_data, company):
        # Swiss QR Bill data in plain text
        if b"SPC\n" in file_data or b"SPC\r\n" in file_data:
            try:
                decoded_data = file_data.decode("utf-8").replace("\r\n", "\n")
                if QR.valid_re.search(decoded_data):
                    return self.parse_qrbill(decoded_data)
            except (UnicodeDecodeError, UserError):
                logger.debug("Failed to decode as UTF-8 or invalid QR-bill data.")
        if decode:
            logger.debug("Search for Swiss QR-Code in PDF file")
            try:
                # TODO support multiple pages
                pdf_img = pdf2image.convert_from_bytes(file_data)[0].convert("RGB")
                pdf_img = np.array(pdf_img)
                # Convert RGB to BGR
                pdf_img = pdf_img[:, :, ::-1].copy()

                qr_list = self._read_swiss_qr_code(pdf_img)
                if qr_list:
                    decoded_data = qr_list[0].data.decode().replace("\r\n", "\n")
                    logger.debug(
                        "Swiss QR-Code decoded from PDF file %s" % decoded_data
                    )
                    return self.parse_qrbill(decoded_data)
            except Exception:
                logger.debug("Failed to parse as PDF")
            logger.debug("No Swiss QR-Code found in PDF file")
        return super().parse_pdf_invoice(file_data, company)
