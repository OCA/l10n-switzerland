##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    @author: Cyril Sester <cyril.sester@outlook.com>
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

from openerp.osv import orm
from openerp import netsvc
from openerp.tools.translate import _


class invoice(orm.Model):

    ''' Inherit invoice to add invoice freeing functionality. It's about
        moving related payment line in a new cancelled payment order. This
        way, the invoice (properly, invoice's move lines) can be used again
        in another payment order.
    '''
    _inherit = 'account.invoice'

    def cancel_payment_lines(self, cr, uid, ids, context=None):
        ''' This function simply find related payment lines and move them
            in a new payment order.
        '''
        mov_line_obj = self.pool.get('account.move.line')
        pay_line_obj = self.pool.get('payment.line')
        pay_order_obj = self.pool.get('payment.order')

        active_ids = context.get('active_ids')
        move_ids = [inv.move_id.id for inv in self.browse(cr, uid,
                                                          active_ids, context)]
        move_line_ids = mov_line_obj.search(
            cr, uid, [('move_id', 'in', move_ids)], context=context)

        pay_line_ids = pay_line_obj.search(
            cr, uid, [('move_line_id', 'in', move_line_ids)], context=context)
        if not pay_line_ids:
            raise orm.except_orm('RuntimeError', _('No payment line found !'))

        old_pay_order = pay_line_obj.browse(cr, uid, pay_line_ids[0]).order_id
        vals = {
            'date_created': old_pay_order.date_created,
            'date_prefered': old_pay_order.date_prefered,
            'payment_order_type': old_pay_order.payment_order_type,
            'mode': old_pay_order.mode.id,
        }

        pay_order_id = pay_order_obj.create(cr, uid, vals, context)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'payment.order', pay_order_id, 'cancel',
                                cr)
        pay_line_obj.write(cr, uid, pay_line_ids, {'order_id': pay_order_id},
                           context)

        return pay_order_id


class account_invoice_free(orm.TransientModel):

    ''' Wizard to free invoices. When job is done, user is redirected on new
        payment order.
    '''
    _name = 'account.invoice.free'

    def invoice_free(self, cr, uid, ids, context=None):
        inv_obj = self.pool.get('account.invoice')

        order_id = inv_obj.cancel_payment_lines(cr, uid, ids, context)

        action = {
            'name': 'Payment order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form, tree',
            'res_model': 'payment.order',
            'res_id': order_id,
            'target': 'current',
        }

        return action
