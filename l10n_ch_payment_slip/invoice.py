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


class AccountMoveLine(Model):

    _inherit = "account.move.line"

    _compile_get_ref = re.compile('[^0-9]')

    _columns = {
        'transaction_ref': fields.char('Transaction Ref.', size=128),
    }

    def init(self, cr):
        cr.execute('UPDATE account_move_line SET transaction_ref = ref'
                   '  WHERE transaction_ref IS NULL'
                   '   AND ref IS NOT NULL')
        return True

    def get_bvr_ref(self, cursor, uid, move_line_id, context=None):
        """Retrieve ESR/BVR reference from move line in order to print it"""
        res = ''
        if isinstance(move_line_id, (tuple, list)):
            assert len(move_line_id) == 1, "Only 1 ID expected"
            move_line_id = move_line_id[0]
        move_line = self.browse(cursor, uid, move_line_id, context=context)
        ## We check if the type is bvr, if not we return false
        if move_line.invoice.partner_bank_id.state != 'bvr':
            return ''
        ##
        if move_line.invoice.partner_bank_id.bvr_adherent_num:
            res = move_line.invoice.partner_bank_id.bvr_adherent_num
        move_number = ''
        if move_line.invoice.number:
            move_number = self._compile_get_ref.sub('', str(move_line.invoice.number) + str(move_line_id))
        return mod10r(res + move_number.rjust(26 - len(res), '0'))


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
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        tier_account_id = account_obj.search(cursor, uid, [('type', 'in', ['receivable', 'payable'])])
        for inv in self.browse(cursor, uid, ids, context=context):
            move_lines = move_line_obj.search(cursor, uid, [('move_id', '=', inv.move_id.id),
                                                            ('account_id', 'in', tier_account_id)])
            if move_lines:
                if len(move_lines) == 1:
                    res[inv.id] = self._space(inv.get_bvr_ref())
                else:
                    refs = []
                    for move_line in move_line_obj.browse(cursor, uid, move_lines, context=context):
                        refs.append(self._space(move_line.get_bvr_ref()))
                    res[inv.id] = ' ; '.join(refs)
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
            self._space('123456789012345')
            '12 34567 89012 345'
        """
        return ''.join([' '[(i - 2) % nbrspc:] + c for i, c in enumerate(nbr)])

    def _update_ref_on_account_analytic_line(self, cr, uid, ref, move_id, context=None):
        cr.execute('UPDATE account_analytic_line SET ref=%s'
                   '   FROM account_move_line '
                   ' WHERE account_move_line.move_id = %s '
                   '   AND account_analytic_line.move_id = account_move_line.id',
                   (ref, move_id))
        return True

    def action_number(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).action_number(cr, uid, ids, context=context)
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        tier_account_id = account_obj.search(cr, uid, [('type', 'in', ['receivable', 'payable'])])

        for inv in self.browse(cr, uid, ids, context=context):
            if inv.type != 'out_invoice' and inv.partner_bank_id.state != 'bvr':
                continue
            move_lines = move_line_obj.search(cr, uid, [('move_id', '=', inv.move_id.id),
                                                        ('account_id', 'in', tier_account_id)])
            # We keep this branch for compatibility with single BVR report.
            # This should be cleaned when porting to V8
            if move_lines:
                if len(move_lines) == 1:
                    ref = inv.get_bvr_ref()
                    move_id = inv.move_id
                    if move_id:
                        cr.execute('UPDATE account_move_line SET transaction_ref=%s'
                                   '  WHERE move_id=%s',
                                   (ref, move_id.id))
                        self._update_ref_on_account_analytic_line(cr, uid, ref, move_id.id)
                else:
                    for move_line in move_line_obj.browse(cr, uid, move_lines, context=context):
                        ref = move_line.get_bvr_ref()
                        if ref:
                            cr.execute('UPDATE account_move_line SET transaction_ref=%s'
                                       '  WHERE id=%s',
                                       (ref, move_line.id))
                            self._update_ref_on_account_analytic_line(cr, uid, ref,
                                                                      move_line.move_id.id)
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
