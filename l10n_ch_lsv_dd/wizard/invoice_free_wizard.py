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

from openerp import models, api


class AccountInvoiceFree(models.TransientModel):

    ''' Wizard to free invoices. When job is done, user is redirected on new
        payment order.
    '''
    _name = 'account.invoice.free'

    @api.multi
    def invoice_free(self):
        inv_obj = self.env['account.invoice']
        order = inv_obj.cancel_payment_lines()
        action = {
            'name': 'Payment order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form, tree',
            'res_model': 'payment.order',
            'res_id': order.id,
            'target': 'current',
        }

        return action
