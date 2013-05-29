# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
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
import re

from openerp.osv.orm import Model, fields
from openerp.tools import mod10r


class AccountInvoice(Model):
    """Inherit account.invoice in order to add bvr
    printing functionnalites. BVR is a Swiss payment vector"""
    _inherit = "account.invoice"

    _compile_get_ref = re.compile('[^0-9]')

    def _get_reference_type(self, cursor, user, context=None):
        """Function use by the function field reference_type in order to initalise available
        BVR Reference Types"""
        res = super(AccountInvoice, self)._get_reference_type(cursor, user,
                                                              context=context)
        res.append(('bvr', 'BVR'))
        return res

    def _compute_full_bvr_name(self, cursor, uid, ids, field_names, arg, context=None):
        res = {}
        for inv in self.browse(cursor, uid, ids, context=context):
            res[inv.id] = self._space(inv.get_bvr_ref())
        return res

    _columns = {
        ### BVR reference type BVR or FREE
        'reference_type': fields.selection(_get_reference_type,
                                           'Reference Type', required=True),
        ### Partner bank link between bank and partner id
        'partner_bank_id': fields.many2one('res.partner.bank', 'Bank Account',
                                           help='The partner bank account to pay\nKeep empty to use the default'),
        'bvr_reference': fields.function(_compute_full_bvr_name, type="char", size=512, string="BVR REF.",
                                         store=True, readonly=True)
    }

    def get_bvr_ref(self, cursor, uid, inv_id, context=None):
        """Retrieve ESR/BVR reference form invoice in order to print it"""
        res = ''
        if isinstance(inv_id, list):
            inv_id = inv_id[0]
        inv = self.browse(cursor, uid, inv_id, context=context)
        ## We check if the type is bvr, if not we return false
        if inv.partner_bank_id.state != 'bvr':
            return ''
        ##
        if inv.partner_bank_id.bvr_adherent_num:
            res = inv.partner_bank_id.bvr_adherent_num
        invoice_number = ''
        if inv.number:
            invoice_number = self._compile_get_ref.sub('', inv.number)
        return mod10r(res + invoice_number.rjust(26 - len(res), '0'))

    def _space(self, nbr, nbrspc=5):
        """Spaces * 5.

        Example:
            >>> self._space('123456789012345')
            '12 34567 89012 345'
        """
        return ''.join([' '[(i - 2) % nbrspc:] + c for i, c in enumerate(nbr)])

    def action_number(self, cursor, uid, ids, context=None):
        res = super(AccountInvoice, self).action_number(cursor, uid, ids, context=context)
        for inv in self.browse(cursor, uid, ids, context=context):
            if inv.type != 'out_invoice' or inv.partner_bank_id.state != 'bvr':
                continue
            ref = inv.get_bvr_ref()
            move_id = inv.move_id
            if move_id:
                cursor.execute('UPDATE account_move SET ref=%s'
                               '  WHERE id=%s',
                               (ref, move_id.id))
                cursor.execute('UPDATE account_move_line SET ref=%s'
                               '  WHERE move_id=%s',
                               (ref, move_id.id))
                cursor.execute('UPDATE account_analytic_line SET ref=%s'
                               '   FROM account_move_line '
                               ' WHERE account_move_line.move_id = %s '
                               '   AND account_analytic_line.move_id = account_move_line.id',
                               (ref, move_id.id))
        return res

    def copy(self, cursor, uid, inv_id, default=None, context=None):
        default = default or {}
        default.update({'reference': False})
        return super(AccountInvoice, self).copy(cursor, uid, inv_id, default, context)


class AccountTaxCode(Model):
    """Inherit account tax code in order
    to add a Case code"""
    _name = 'account.tax.code'
    _inherit = "account.tax.code"
    _columns = {
        'code': fields.char('Case Code', size=512),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
