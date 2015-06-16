# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville, Nicolas Bessi Copyright 2013 Camptocamp SA
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
from openerp import models


class BVRFromCreditControl(models.AbstractModel):
    _name = 'report.slip_from_credit_control'


class ExtendedReport(models.Model):
    """Print pay slip form credit line"""

    _inherit = "report"

    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
        if context is None:
            context = {}
        company = self.pool['res.users'].browse(cr, uid, uid,
                                                context=context).company_id
        if report_name == 'slip_from_credit_control':
            cr_line_obj = self.pool['credit.control.line']
            slip_obj = self.pool['l10n_ch.payment_slip']
            slips = []
            for cr_line in cr_line_obj.browse(cr, uid, ids, context=context):
                slips_ids = slip_obj.search(
                    cr, uid,
                    [('move_line_id', '=', cr_line.move_line_id.id)],
                    context=context
                )
                if not slips_ids:
                    continue
                ctx = dict(context, __slip_credit_control_line_id=cr_line.id)
                slips += slip_obj.browse(cr, uid, slips_ids, context=ctx)
            if len(slips) == 1:
                return slips[0]._draw_payment_slip(a4=True, b64=False,
                                                   out_format='PDF')
            if company.merge_mode == 'in_memory':
                return self.merge_pdf_in_memory(slips)
            return self.merge_pdf_on_disk(slips)
        else:
            return super(ExtendedReport, self).get_pdf(
                cr, uid, ids, report_name,
                html=html, data=data, context=context
            )
