# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
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

from openerp.tools.translate import _
from openerp.osv import orm, fields
from openerp.addons.account_statement_base_completion.statement import (
    ErrorTooManyPartner
)


class account_statement_completion_rule(orm.Model):
    """ Add a rule based on BVR Reference """
    _inherit = "account.statement.completion.rule"

    def _get_functions(self, cr, uid, context=None):
        res = super(account_statement_completion_rule, self).\
            _get_functions(cr, uid, context=context)
        res.append(('get_from_bvr_reference_and_invoice',
                    'Match Invoice using BVR/ESR Reference'))
        return res

    _columns = {
        'function_to_call': fields.selection(_get_functions, 'Method'),
    }

    def get_from_bvr_reference_and_invoice(self, cr, uid, st_line, context=None):
        """
        Match the partner based on the BVR reference field of the invoice.
        Then, call the generic st_line method to complete other values.

        In that case, we always fulfill the reference of the line with
        the invoice name.

        :param dict st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id' : value,
            ...}
            """
        st_obj = self.pool.get('account.bank.statement.line')
        res = {}
        invoice_obj = self.pool.get('account.invoice')
        # For customer invoices, search in bvr_reference that is as list
        # of references separated by semicolons and formatted with
        # spaces inside them.
        # For supplier invoices, search in 'reference'
        query = ("SELECT id FROM account_invoice "
                 "WHERE company_id = %s "
                 "AND (%s = ANY (string_to_array( "
                 "                 replace(bvr_reference, ' ', ''), "
                 "               ';')) "
                 "     AND type IN ('out_invoice', 'out_refund') "
                 "     OR type IN ('in_invoice', 'in_refund') "
                 "     AND reference_type = 'bvr' AND reference = %s "
                 ")")
        cr.execute(query, (st_line['company_id'][0],
                           st_line['transaction_id'],
                           st_line['transaction_id']))
        rows = cr.fetchall()
        invoice_ids = [row[0] for row in rows]
        if len(invoice_ids) > 1:
            raise ErrorTooManyPartner(
                _('Line named "%s" (Ref:%s) was matched by more than '
                  'one partner.') % (st_line['name'], st_line['ref']))
        elif len(invoice_ids) == 1:
            invoice = invoice_obj.browse(cr, uid, invoice_ids[0],
                                         context=context)
            res['partner_id'] = invoice.partner_id.id
            # we want the move to have the same ref than the found
            # invoice's move, thus it will be easier to link them for the
            # accountants
            if invoice.move_id:
                res['ref'] = invoice.move_id.ref
            st_vals = st_obj.get_values_for_line(
                cr, uid,
                profile_id=st_line['profile_id'],
                master_account_id=st_line['master_account_id'],
                partner_id=res.get('partner_id', False),
                line_type=st_line['type'],
                amount=st_line['amount'] if st_line['amount'] else 0.0,
                context=context)
            res.update(st_vals)
        return res
