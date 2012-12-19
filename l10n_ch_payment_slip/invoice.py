# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Donors: Hasa Sàrl, Open Net Sàrl and Prisme Solutions Informatique SA
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

from datetime import datetime
from openerp.osv.orm import Model, fields
from tools import mod10r

class AccountInvoice(Model):
    """Inherit account.invoice in order to add bvr
    printing functionnalites. BVR is a Swiss payment vector"""
    _inherit = "account.invoice"


    def _get_reference_type(self, cursor, user, context=None):
        """Function use by the function field reference_type in order to initalise available
        BVR Reference Types"""
        res = super(AccountInvoice, self)._get_reference_type(cursor, user,
                context=context)
        res.append(('bvr', 'BVR'))
        return res



    _columns = {
        ### BVR reference type BVR or FREE
        'reference_type': fields.selection(_get_reference_type,
            'Reference Type', required=True),
        ### Partner bank link between bank and partner id
        'partner_bank_id': fields.many2one('res.partner.bank', 'Bank Account',
            help='The partner bank account to pay\nKeep empty to use the default'),
    }

    def _check_bvr(self, cr, uid, ids, context=None):
        """
        Function to validate a bvr reference like :
        0100054150009>132000000000000000000000014+ 1300132412>
        The validation is based on l10n_ch
        """
        invoices = self.browse(cr,uid,ids)
        for invoice in invoices:
            if invoice.reference_type == 'bvr':
                if not invoice.reference:
                    return False
                ## I need help for this bug because in this case
                # <010001000060190> 052550152684006+ 43435>
                # the reference 052550152684006 do not match modulo 10
                #
                if mod10r(invoice.reference[:-1]) != invoice.reference and \
                    len(invoice.reference) == 15:
                    return True
                #
                if mod10r(invoice.reference[:-1]) != invoice.reference:
                    return False
        return True

    def _check_reference_type(self, cursor, user, ids, context=None):
        """Check the supplier invoice reference type depending
        on the BVR reference type and the invoice partner bank type"""
        for invoice in self.browse(cursor, user, ids):
            if invoice.type in 'in_invoice':
                if invoice.partner_bank_id and \
                        invoice.partner_bank_id.state in \
                        ('bvr', 'bv') and \
                        invoice.reference_type != 'bvr':
                    return False
        return True

    _constraints = [
        (_check_bvr, 'Error: Invalid Bvr Number (wrong checksum).',
            ['reference']),
        (_check_reference_type, 'Error: BVR reference is required.',
            ['reference_type']),
    ]

    def onchange_partner_id(self, cursor, uid, ids, invoice_type, partner_id,
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        """ Function that is call when the partner of the invoice is changed
        it will retrieve and set the good bank partner bank"""
        #context not define in signature of function in account module
        context = {}
        res = super(account_invoice, self).onchange_partner_id(cursor, uid, ids, invoice_type, partner_id,
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False)
        bank_id = False
        if partner_id:
            if invoice_type in ('in_invoice', 'in_refund'):
                p = self.pool.get('res.partner').browse(cursor, uid, partner_id, context)
                if p.bank_ids:
                    bank_id = p.bank_ids[0].id
                res['value']['partner_bank_id'] = bank_id
            else:
                user = self.pool.get('res.users').browse(cursor, uid, uid, context)
                bank_ids = user.company_id.partner_id.bank_ids
                if bank_ids:
                    res['value']['partner_bank_id'] = bank_ids[0]

        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(cursor, uid, ids, bank_id)
            res['value'].update(to_update['value'])
        return res

    def onchange_partner_bank(self, cursor, user, ids, partner_bank_id):
        """update the reference invoice_type depending of the partner bank"""
        res = {'value': {}}
        partner_bank_obj = self.pool.get('res.partner.bank')
        if partner_bank_id:
            partner_bank = partner_bank_obj.browse(cursor, user, partner_bank_id)
            if partner_bank.state in ('bvr', 'bv'):
                res['value']['reference_type'] = 'bvr'
        return res

    def _set_condition(self, cr, uid, inv_id, commentid, key):
        """Set the text of the notes in invoices"""
        if not commentid :
            return {}
        try :
            lang = self.browse(cr, uid, inv_id)[0].partner_id.lang
        except :
            lang = 'en_US'
        cond = self.pool.get('account.condition_text').browse(
            cr, uid, commentid, {'lang': lang})
        return {'value': {key: cond.text}}

    def set_header(self, cr, uid, inv_id, commentid):
        return self._set_condition(cr, uid, inv_id, commentid, 'note1')

    def set_footer(self, cr, uid, inv_id, commentid):
        return self._set_condition(cr, uid, inv_id, commentid, 'note2')



class AccountTaxCode(Model):
    """Inherit account tax code in order
    to add a Case code"""
    _name = 'account.tax.code'
    _inherit = "account.tax.code"
    _columns = {
        'code': fields.char('Case Code', size=512),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
