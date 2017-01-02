# -*- coding: utf-8 -*-
# © 2015 Nicolas Bessi (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from reportlab.lib.units import inch
from openerp import models, api


class PaymentSlip(models.Model):

    _inherit = 'l10n_ch.payment_slip'

    @api.model
    def _draw_background(self, canvas, print_settings):
        """Draw payment slip background based on company setting

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        """
        def _draw_on_canvas():
            canvas.drawImage(self.image_absolute_path('bvr.png'),
                             0, 0, 8.271 * inch, 4.174 * inch)
        report_name = print_settings.report_name
        if report_name == 'invoice_and_one_slip_per_page_from_invoice':
            if print_settings.bvr_background_on_merge:
                _draw_on_canvas()
        else:
            if print_settings.bvr_background:
                _draw_on_canvas()
