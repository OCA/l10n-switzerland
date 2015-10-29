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

from openerp import models, api, _, exceptions


class AccountInvoice(models.Model):

    ''' Inherit invoice to add invoice freeing functionality. It's about
        moving related payment line in a new cancelled payment order. This
        way, the invoice (properly, invoice's move lines) can be used again
        in another payment order.
    '''
    _inherit = 'account.invoice'

    @api.multi
    def cancel_payment_lines(self):
        ''' This function simply finds related payment lines and move them
            in a new payment order.
        '''
        mov_line_obj = self.env['account.move.line']
        pay_line_obj = self.env['payment.line']
        pay_order_obj = self.env['payment.order']
        active_ids = self.env.context.get('active_ids')
        move_ids = self.browse(active_ids).mapped('move_id.id')
        move_line_ids = mov_line_obj.search([('move_id', 'in', move_ids)]).ids
        pay_lines = pay_line_obj.search([('move_line_id',
                                          'in', move_line_ids)])
        if not pay_lines:
            raise exceptions.Warning(_('No payment line found !'))

        old_pay_order = pay_lines[0].order_id
        vals = {
            'date_created': old_pay_order.date_created,
            'date_prefered': old_pay_order.date_prefered,
            'payment_order_type': old_pay_order.payment_order_type,
            'mode': old_pay_order.mode.id,
        }

        pay_order = pay_order_obj.create(vals)
        pay_order.signal_workflow('cancel')
        pay_lines.write({'order_id': pay_order.id})
        return pay_order
