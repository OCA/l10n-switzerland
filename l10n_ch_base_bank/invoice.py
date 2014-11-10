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
<<<<<<< HEAD
<<<<<<< HEAD
from openerp.osv.orm import Model
from openerp.tools import mod10r


class AccountInvoice(Model):

    _inherit = "account.invoice"

    def onchange_partner_id(self, cursor, uid, ids, invoice_type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False):
        """ Function that is call when the partner of the invoice is changed
        it will retrieve and set the good bank partner bank"""
        #context not define in signature of function in account module
        context = {}
        res = super(AccountInvoice, self).onchange_partner_id(cursor, uid, ids, invoice_type, partner_id,
                                                              date_invoice=False, payment_term=False,
                                                              partner_bank_id=False, company_id=False)
        bank_id = False
        if partner_id:
            if invoice_type in ('in_invoice', 'in_refund'):
                p = self.pool.get('res.partner').browse(cursor, uid, partner_id, context)
=======
from openerp import models, fields, api, _
=======
from openerp import models, api, _
>>>>>>> Cleanup of l10n_ch_base_bank port
from openerp.tools import mod10r


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    def onchange_partner_id(self, invoice_type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False,
                            company_id=False):
        """ Function that is call when the partner of the invoice is changed
        it will retrieve and set the good bank partner bank"""
        res = super(AccountInvoice, self).onchange_partner_id(
            invoice_type, partner_id,
            date_invoice=False, payment_term=False,
            partner_bank_id=False, company_id=False
        )
        bank_id = False
        if partner_id:
            if invoice_type in ('in_invoice', 'in_refund'):
<<<<<<< HEAD
                p = self.env['res.partner'].browse(partner_id)
>>>>>>> [ADD] Added l10n_ch_base_bank migrated to the new api
                if p.bank_ids:
                    bank_id = p.bank_ids[0].id
=======
                partner = self.env['res.partner'].browse(partner_id)
                if partner.bank_ids:
                    bank_id = partner.bank_ids[0].id
>>>>>>> Cleanup of l10n_ch_base_bank port
                res['value']['partner_bank_id'] = bank_id
            else:
<<<<<<< HEAD
                user = self.pool.get('res.users').browse(cursor, uid, uid, context)
=======
                user = self.env.user
>>>>>>> [ADD] Added l10n_ch_base_bank migrated to the new api
                bank_ids = user.company_id.partner_id.bank_ids
                if bank_ids:
                    res['value']['partner_bank_id'] = bank_ids[0].id
        if partner_bank_id != bank_id:
<<<<<<< HEAD
            to_update = self.onchange_partner_bank(cursor, uid, ids, bank_id)
            res['value'].update(to_update['value'])
        return res

    def onchange_partner_bank(self, cursor, user, ids, partner_bank_id):
        """update the reference invoice_type depending of the partner bank"""
        res = {'value': {}}
        partner_bank_obj = self.pool.get('res.partner.bank')
        if partner_bank_id:
            partner_bank = partner_bank_obj.browse(cursor, user, partner_bank_id)
            if partner_bank.state == 'bvr':
                res['value']['reference_type'] = 'bvr'
            else:
                res['value']['reference_type'] = 'none'
                
        return res

    def _check_reference_type(self, cursor, user, ids, context=None):
        """Check the supplier invoice reference type depending
        on the BVR reference type and the invoice partner bank type"""
        for invoice in self.browse(cursor, user, ids):
            if invoice.type in 'in_invoice':
                if invoice.partner_bank_id and invoice.partner_bank_id.state == 'bvr' and \
                        invoice.reference_type != 'bvr':
                    return False
        return True

    def _check_bvr(self, cr, uid, ids, context=None):
=======
            res['value']['partner_bank_id'] = bank_id
        return res

    @api.onchange('partner_bank_id')
    def onchange_partner_bank(self):
        """update the reference invoice_type depending of the partner bank"""
        partner_bank = self.partner_bank_id
        if partner_bank:
            if partner_bank.state == 'bvr':
                self.reference_type = 'bvr'
            else:
                self.reference_type = 'none'

    @api.constrains('reference_type')
    def _check_reference_type(self):
        """Check the supplier invoice reference type depending
        on the BVR reference type and the invoice partner bank type"""
        for invoice in self:
            if invoice.type in 'in_invoice':
                if (invoice.partner_bank_id.state == 'bvr' and
                        invoice.reference_type != 'bvr'):
                    raise Warning(
                        _('Invalid Bvr Number (wrong checksum).')
                    )

    @api.constrains('reference')
    def _check_bvr(self):
>>>>>>> [ADD] Added l10n_ch_base_bank migrated to the new api
        """
        Function to validate a bvr reference like :
        0100054150009>132000000000000000000000014+ 1300132412>
        The validation is based on l10n_ch
        """
<<<<<<< HEAD
        invoices = self.browse(cr, uid, ids)
        for invoice in invoices:
            if invoice.reference_type == 'bvr' and invoice.state != 'draft':
                if not invoice.reference:
                    return False
=======
        for invoice in self:
            if invoice.reference_type == 'bvr' and invoice.state != 'draft':
                if not invoice.reference:
                    raise Warning(
                        _('Invalid Bvr Number (wrong checksum).')
                    )
<<<<<<< HEAD
>>>>>>> [ADD] Added l10n_ch_base_bank migrated to the new api
                ## In this case
=======
                # In this case
>>>>>>> Cleanup of l10n_ch_base_bank port
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

<<<<<<< HEAD
<<<<<<< HEAD
    _constraints = [
        (_check_bvr, 'Error: Invalid Bvr Number (wrong checksum).',
            ['reference']),
        (_check_reference_type, 'Error: BVR reference is required.',
            ['reference_type']),
    ]



    # We can not use _default as we need invoice type
    def create(self, cursor, uid, vals, context=None):
        """We override create in order to have customer invoices
        generated by the comercial flow as on change partner is
        not systemtically call"""
        if context is None:
            context = {}
        # In his great wisdom OpnERP allows type to be implicitely set in context
        type_defined = vals.get('type') or context.get('type') or False
        if type_defined == 'out_invoice' and not vals.get('partner_bank_id'):
            user = self.pool.get('res.users').browse(cursor, uid, uid, context=context)
            bank_ids = user.company_id.partner_id.bank_ids
            if bank_ids:
                vals['partner_bank_id'] = bank_ids[0].id
        return super(AccountInvoice, self).create(cursor, uid, vals, context=context)
=======
    # We can not use _default as we need invoice type
=======
>>>>>>> Cleanup of l10n_ch_base_bank port
    @api.model
    def create(self, vals):
        """We override create in order to have customer invoices
        generated by the comercial flow as on change partner is
        not systemtically call"""
        type_defined = vals.get('type') or self.env.context.get('type', False)
        if type_defined == 'out_invoice' and not vals.get('partner_bank_id'):
            user = self.env.user
            bank_ids = user.company_id.partner_id.bank_ids
            if bank_ids:
                vals['partner_bank_id'] = bank_ids[0].id
        return super(AccountInvoice, self).create(vals)
<<<<<<< HEAD
>>>>>>> [ADD] Added l10n_ch_base_bank migrated to the new api
=======
>>>>>>> Cleanup of l10n_ch_base_bank port
