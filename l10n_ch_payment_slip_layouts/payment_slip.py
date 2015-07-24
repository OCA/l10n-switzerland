# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
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
