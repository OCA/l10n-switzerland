# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
from openerp import api, models


class BVRFromInvoice(models.AbstractModel):
    _name = 'report.payment_slip_from_invoice'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(
            'l10n_ch_payment_slip.one_slip_per_page'
        )
        slip_model = self.env['l10n_ch.payment_slip']
        docs = slip_model.compute_slip_from_invoices(self)
        docargs = {
            'doc_ids': docs._ids,
            'doc_model': report.model,
            'docs': docs,
        }
        return report_obj.render(
            'l10n_ch_payment_slip.one_slip_per_page',
            docargs
        )
