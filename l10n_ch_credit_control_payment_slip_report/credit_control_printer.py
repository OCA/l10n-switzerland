# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2013 Camptocamp SA
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
import base64

from openerp.osv import orm
from openerp.tools.translate import _


class CreditControlPrinter(orm.TransientModel):
    """Print lines"""
    _inherit = 'credit.control.printer'

    def print_linked_bvr(self, cr, uid, wiz_id, context=None):
        assert not (isinstance(wiz_id, list) and len(wiz_id) > 1), \
            "wiz_id: only one id expected"
        comm_obj = self.pool.get('credit.control.communication')
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        form = self.browse(cr, uid, wiz_id, context)

        if not form.line_ids and not form.print_all:
            raise orm.except_orm(_('Error'),
                                 _('No credit control lines selected.'))

        move_line_ids = []
        for line in form.line_ids:
            if line.move_line_id:
                move_line_ids.append(line.move_line_id.id)
        report_file = comm_obj._generate_report_bvr(cr, uid,
                                                    move_line_ids,
                                                    context=context)

        form.write({'report_file': base64.b64encode(report_file),
                    'state': 'done'})

        return {'type': 'ir.actions.act_window',
                'res_model': 'credit.control.printer',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': form.id,
                'views': [(False, 'form')],
                'target': 'new',
                }
