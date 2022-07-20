# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, models

from reportlab.graphics.barcode import createBarcodeDrawing


class IrActionsReport(models.Model):

    _inherit = "ir.actions.report"

    @api.model
    def qrcode(self, value, width=600, height=100, bar_border=4):
        try:
            width, height, bar_border = (
                int(width),
                int(height),
                int(bar_border),
            )

            qrcode = createBarcodeDrawing(
                "QR",
                value=value,
                format='png',
                width=width,
                height=height,
                barBorder=bar_border,
            )
            return qrcode.asString('png')
        except (ValueError, AttributeError):
            raise ValueError("Cannot convert into QR code.")
