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

from openerp import pooler
from openerp.addons.report_webkit import webkit_report


class MultiBvrWebKitParser(webkit_report.WebKitParser):

    def create_single_pdf(self, cursor, uid, ids,
                          data, report_xml, context=None):
        self.pool = pooler.get_pool(cursor.dbname)
        target_obj = 'account.move.line'
        move_line_ids = self.get_obj_reference(cursor, uid, ids, context=context)
        ctx_multi_bvr = context.copy()
        ctx_multi_bvr['active_model'] = self.table = target_obj
        ctx_multi_bvr['active_ids'] = move_line_ids
        return super(MultiBvrWebKitParser, self
                     ).create_single_pdf(cursor, uid, move_line_ids,
                                         data, report_xml, ctx_multi_bvr)

    def get_obj_reference(self, cursor, uid, ids, context=None):
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        invoice_obj = self.pool.get('account.invoice')
        inv = invoice_obj.browse(cursor, uid, ids[0], context=context)
        tier_account_ids = account_obj.search(
            cursor, uid,
            [('type', 'in', ['receivable', 'payable'])],
            context=context)
        move_line_ids = move_line_obj.search(
            cursor, uid,
            [('move_id', '=', inv.move_id.id),
             ('account_id', 'in', tier_account_ids)],
            context=context)
        return move_line_ids
