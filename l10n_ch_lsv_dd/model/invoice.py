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

from openerp import models, api, _
from openerp import netsvc
from openerp import exceptions


class invoice(models.Model):

    ''' Inherit invoice to add invoice freeing functionality. It's about
        moving related payment line in a new cancelled payment order. This
        way, the invoice (properly, invoice's move lines) can be used again
        in another payment order.
    '''
    _inherit = 'account.invoice'

    @api.multi
    def cancel_payment_lines(self):
        ''' This function simply find related payment lines and move them
            in a new payment order.
        '''
        mov_line_obj = self.env['account.move.line']
        pay_line_obj = self.env['payment.line']
        pay_order_obj = self.env['payment.order']

        active_ids = self.env.context.get('active_ids')
        move_ids = [inv.move_id.id for inv in self.browse(active_ids)]
        move_ids = [inv.move_id.id for inv in self.browse(active_ids)]
        move_line_ids = mov_line_obj.search(
            [('move_id', 'in', move_ids)], 
            context=self.env.context
        )

        pay_line_ids = pay_line_obj.search(
            [('move_line_id', 'in', move_line_ids)],
            context=self.env.context
        )
        if not pay_line_ids:
            raise exceptions.Warning(_('No payment line found !'))

        old_pay_order = pay_line_obj.browse(pay_line_ids[0]).order_id
        vals = {
            'date_created': old_pay_order.date_created,
            'date_prefered': old_pay_order.date_prefered,
            'payment_order_type': old_pay_order.payment_order_type,
            'mode': old_pay_order.mode.id,
        }

        pay_order_id = pay_order_obj.create(vals)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate('payment.order', pay_order_id, 'cancel')
        pay_line_obj.write(pay_line_ids, {'order_id': pay_order_id})

        return pay_order_id


class account_invoice_free(models.TransientModel):

    ''' Wizard to free invoices. When job is done, user is redirected on new
        payment order.
    '''
    _name = 'account.invoice.free'

    @api.multi
    def invoice_free(self):
        inv_obj = self.env['account.invoice']

        order_id = inv_obj.cancel_payment_lines()

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
