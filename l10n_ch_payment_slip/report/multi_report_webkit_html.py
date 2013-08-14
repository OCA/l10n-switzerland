# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Romain Deheele. Copyright Camptocamp SA
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

from .report_webkit_html import L10nCHReportWebkitHtml
from .webkit_parser import MultiBvrWebKitParser

from openerp.osv.osv import except_osv
from openerp.tools.translate import _

class L10nCHReportWebkitHtmlMulti(L10nCHReportWebkitHtml):
    def __init__(self, cr, uid, name, context):
        super(L10nCHReportWebkitHtmlMulti, self).__init__(cr, uid, name, context=context)

    def _check(self, move_ids):
        cursor = self.cr
        pool = self.pool
        move_line_obj = pool.get('account.move.line')
        if not move_ids:
            raise except_osv(_('UserError'),
                             _('Your invoice should be validated to generate BVR references.'))
        invoice_id = move_line_obj.read(cursor, self.uid, move_ids[0], ['invoice'])['invoice'][0]
        if invoice_id:
            return super(L10nCHReportWebkitHtmlMulti, self)._check([invoice_id])

MultiBvrWebKitParser('report.invoice_bvr_webkit_multi',
                      'account.invoice',
                      'l10n_ch_payment_slip/report/multi_bvr.mako',
                      parser=L10nCHReportWebkitHtmlMulti)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
