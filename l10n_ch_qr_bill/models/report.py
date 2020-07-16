# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models

from reportlab.graphics.barcode import createBarcodeDrawing


class Report(models.Model):
    _inherit = 'report'

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
