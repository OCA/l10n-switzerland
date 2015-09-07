# -*- coding: utf-8 -*-
#
#  File: wizard/wiz_end_repair.py
#  Module: l10n_ch_scan_bvr
#
##############################################################################
#
#    Author: Nicolas Bessi, Vincent Renaville
#    Copyright 2012 Camptocamp SA
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


from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp.tools import mod10r
import time


class WizardScanBvr(models.TransientModel):
    _name = 'scan.bvr'
    _description = 'BVR/ESR Scanning Wizard'

    # ------------------------- Fields management

    # Base fields
    bvr_string = fields.Char(
        string='BVR string', size=128, required=True,
        help="The line at the bottom right of the BVR"
    )
    journal = fields.Many2one(
        'account.journal', string='Journal',
        required=True, domain=[('type', 'in', ['purchase'])]
    )

    # Complementary fields,
    #   should be filled automatically if anything goes right
    partner = fields.Many2one(
        'res.partner', 'Partner', required=True,
        help="""The supplier who send the invoice.
If it is not set you have to create it"""
    )
    account = fields.Many2one(
        'res.partner.bank', string='Partner bank account',
        required=True, help="""The bank account of the supplier.
If it is not set you have to create it"""
    )
    currency = fields.Many2one('res.currency', string='Currency')
    amount = fields.Float(string='Amount')
    product = fields.Many2one(
        'product.product', string='Related product',
        help="""The product related to the supplier.
If set the invoice line will use it automatically."""
    )

    # ------------------------- Interface related

    @api.multi
    def do_create_invoice(self):
        for wiz in self:
            return self._create_invoice(
                wiz.bvr_string, wiz.product, wiz.account, wiz.journal)

        return False

    @api.multi
    def on_change_bvr_string(self, bvr_str):
        vals = {
            'partner': False,
            'account': False,
            'currency': False,
        }
        bvr_struct = self._get_bvr_structurated(bvr_str)
        if bvr_struct:
            partner_bank_obj = self.env['res.partner.bank']
            conds = [('acc_number', '=', bvr_struct[bvr_struct['domain']])]
            for partner_bank in partner_bank_obj.search(conds):
                vals = {
                    'partner': partner_bank.partner_id.id,
                    'account': partner_bank.id,
                }
                break

            conds = [('name', '=', bvr_struct.get('currency', ''))]
            for currency in self.env['res.currency'].search(conds):
                vals['currency'] = currency.id
                break
            vals['amount'] = bvr_struct['amount']

        return {'value': vals}

    @api.multi
    def on_change_partner(self, partner_id):
        vals = {
            'account': False,
            'product': False,
        }

        conds = [('partner_id', '=', partner_id)]
        for partner_bank in self.env['res.partner.bank'].search(conds):
            vals = {
                'account': partner_bank.id,
            }
            break
        supplier = self.env['res.partner'].browse(partner_id)
        if supplier and supplier.supplier_invoice_default_product:
            vals['product'] = supplier.supplier_invoice_default_product.id

        return {'value': vals}

    # ------------------------- Tools

    @api.model
    def _get_invoice_address(self, partner_id):
        cr, uid, context = self.env.args
        addresses = self.pool['res.partner'].address_get(
            cr, uid, [partner_id], adr_pref='invoice', context=context
        )
        adr_id = addresses and addresses.get(
            'invoice', addresses.get('default', False)) or False
        if not adr_id:
            raise except_orm(
                _('Address Error'), _('No Address Assign to this partner'))
        return adr_id

    def _construct_bvrplus_in_chf(self, bvr_string):
        if len(bvr_string) != 43:
            raise except_orm(
                _('Account Error'), _('BVR CheckSum Error Première partie'))
        if mod10r(bvr_string[0:2]) != bvr_string[0:3]:
            raise except_orm(
                _('Account Error'), _('BVR CheckSum Error Deuxième partie'))
        if mod10r(bvr_string[4:30]) != bvr_string[4:31]:
            raise except_orm(
                _('Account Error'), _('BVR CheckSum Error troisème partie'))
        if mod10r(bvr_string[33:41]) != bvr_string[33:42]:
            raise except_orm(
                _('Account Error'), _('BVR CheckSum Error 4 partie'))

        bvr_struct = {
            'type': bvr_string[0:2],
            'amount': 0.0,
            'reference': bvr_string[4:31],
            'bvrnumber': bvr_string[4:10],
            'beneficiaire': self._create_bvr_account(bvr_string[33:42]),
            'domain': 'beneficiaire',
            'currency': ''
        }

        return bvr_struct

    def _construct_bvr_in_chf(self, bvr_string):
        if len(bvr_string) != 53:
            raise except_orm(
                _('Account Error'), _('BVR CheckSum Error Première partie'))
        if mod10r(bvr_string[0:12]) != bvr_string[0:13]:
            raise except_orm(
                _('AccountError'), _('BVR CheckSum Error Deuxième partie'))
        if mod10r(bvr_string[14:40]) != bvr_string[14:41]:
            raise except_orm(
                _('Account Error'), _('BVR CheckSum Error troisème partie'))
        if mod10r(bvr_string[43:51]) != bvr_string[43:52]:
            raise except_orm(
                _('AccountError'), _('BVR CheckSum Error 4 partie'))

        bvr_struct = {
            'type': bvr_string[0:2],
            'amount': float(bvr_string[2:12])/100,
            'reference': bvr_string[14:41],
            'bvrnumber': bvr_string[14:20],
            'beneficiaire': self._create_bvr_account(bvr_string[43:52]),
            'domain': 'beneficiaire',
            'currency': ''
        }

        return bvr_struct

    def _construct_bvr_postal_in_chf(self, bvr_string):
        if len(bvr_string) != 42:
            raise except_orm(
                _('Account Error'), _('BVR CheckSum Error Première partie'))

        bvr_struct = {
            'type': bvr_string[0:2],
            'amount': float(bvr_string[2:12])/100,
            'reference': bvr_string[14:30],
            'bvrnumber': '',
            'beneficiaire': self._create_bvr_account(bvr_string[32:41]),
            'domain': 'beneficiaire',
            'currency': ''
        }

        return bvr_struct

    def _construct_bvr_postal_other_in_chf(self, bvr_string):
        if len(bvr_string) != 41:
            raise except_orm(
                _('Account Error'), _('BVR CheckSum Error Première partie'))

        bvr_struct = {
            'type': bvr_string[0:2],
            'amount': float(bvr_string[7:16])/100,
            'reference': bvr_string[18:33],
            'bvrnumber': '000000',
            'beneficiaire': self._create_bvr_account(bvr_string[34:40]),
            'domain': 'beneficiaire',
            'currency': ''
        }

        return bvr_struct

    def _create_invoice(self, bvr_string, product, account_info, journal):
        bvr_struct = self._get_bvr_structurated(bvr_string)

        # We will now search the currency_id
        #

        conds = [('name', '=', bvr_struct['currency'])]
        currency_search = self.env['res.currency'].search(conds)
        currency_id = currency_search[0].id

        date_due = time.strftime('%Y-%m-%d')

        # We will now compute the due date and fixe the payment term
        payment_term_id = account_info.partner_id.property_payment_term and \
            account_info.partner_id.property_payment_term.id or False
        if payment_term_id:
            # We Calculate due_date
            inv_obj = self.env['account.invoice']
            res = inv_obj.onchange_payment_term_date_invoice(
                payment_term_id, time.strftime('%Y-%m-%d'))
            date_due = res['value']['date_due']
        #
        #
        valid_types = {'purchase': 'in_invoice', 'sale': 'out_invoice'}
        inv_type = valid_types.get(journal.type, False)
        if not inv_type:
            raise except_orm(
                _('Journal Type Error'),
                _('Invalid journal selected: must be for purchases or sales!'))
        if inv_type == 'in_invoice':
            account = account_info.partner_id.property_account_payable
        else:
            account = account_info.partner_id.property_account_receivable
        add_inv_id = self._get_invoice_address(account_info.partner_id.id)
        curr_invoice = {
            'name': time.strftime('%Y-%m-%d'),
            'partner_id': account_info.partner_id.id,
            'address_invoice_id': add_inv_id,
            'account_id': account.id,
            'date_due': date_due,
            'date_invoice': time.strftime('%Y-%m-%d'),
            'payment_term': payment_term_id,
            'reference_type': 'bvr',
            'reference':  bvr_struct['reference'],
            'amount_total':  bvr_struct['amount'],
            'check_total':  bvr_struct['amount'],
            'partner_bank_id': account_info.id,
            'comment': '',
            'currency_id': currency_id,
            'journal_id':  journal.id,
            'type': inv_type,
        }

        last_invoice = self.env['account.invoice'].create(curr_invoice)
        invoices = [last_invoice.id]

        invoice_line = {
            'name': 'BVR ' + bvr_struct['reference'],
            'invoice_id': last_invoice.id,
            'price_unit': bvr_struct['amount'],
            'quantity': 1,
        }
        invl_obj = self.env['account.invoice.line']
        if product:
            vals = invl_obj.product_id_change(
                product.id, product.uom_id.id, qty=1,
                name='', type=inv_type, partner_id=account_info.partner_id.id,
                fposition_id=False, price_unit=product.lst_price,
                currency_id=False, company_id=None)
            if vals.get('value', {}):
                invoice_line.update(vals['value'])
                invoice_line['invoice_line_tax_id'] = \
                    [(6, 0, invoice_line['invoice_line_tax_id'])]
        invl_obj.create(invoice_line)

        journal_type = {
            'in_invoice': 'purchase',
            'out_invoice': 'sale'
        }[inv_type]

        ctx = "{'type':'%s', 'journal_type': '%s'}" % (inv_type, journal_type)

        return {
            'domain': "[('id', 'in', ["+','.join(map(str, invoices))+"])]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'account.invoice',
            'context': ctx,
            'type': 'ir.actions.act_window',
            'res_id': invoices
        }

    def _create_bvr_account(self, account_unformated):
        account_formated = account_unformated[0:2] + '-'
        val = account_unformated[2:len(account_unformated)-1]
        account_formated += str(int(val)) + '-'
        i = len(account_unformated)-1
        j = len(account_unformated)
        account_formated += account_unformated[i:j]

        return account_formated

    def _get_bvr_structurated(self, bvr_string):
        # Here are a few examples:
        #
        # BVR Standrard
        # 0100003949753>120000000000234478943216899+ 010001628>
        # BVR without BVr Reference
        # 0100000229509>000000013052001000111870316+ 010618955>
        # BVR + In CHF
        # 042>904370000000000000007078109+ 010037882>
        # BVR In euro
        # 2100000440001>961116900000006600000009284+ 030001625>
        # <060001000313795> 110880150449186+ 43435>
        # <010001000165865> 951050156515104+ 43435>
        # <010001000060190> 052550152684006+ 43435>
        # Other examples:
        # 0100000158305>000000000477960700004692148+ 010496631>
        # 0100000080504>000924738899018808000920133+ 010230504>

        if not bvr_string:
            return False

        # We will get the 2 frist digit of the BVr string in order
        # to now the BVR type of this account
        bvr_type = bvr_string[0:2]
        if bvr_type == '01' and len(bvr_string) == 42:
            # Type: BVR in CHF
            bvr_struct = self._construct_bvr_postal_in_chf(bvr_string)

            # We will set the currency , in this case it's allways CHF
            bvr_struct['currency'] = 'CHF'

        elif bvr_type == '01':
            # Type: BVR in CHF
            bvr_struct = self._construct_bvr_in_chf(bvr_string)

            # We will set the currency , in this case it's allways CHF
            bvr_struct['currency'] = 'CHF'

        elif bvr_type == '03':
            # At this time: same as a standard BVR with 01 code
            bvr_struct = self._construct_bvr_postal_in_chf(bvr_string)

            # We will set the currency , in this case it's allways CHF
            bvr_struct['currency'] = 'CHF'

        elif bvr_type == '04':
            # Type: postal BVR in CHF
            bvr_struct = self._construct_bvrplus_in_chf(bvr_string)

            # We will set the currency , in this case it's allways CHF
            bvr_struct['currency'] = 'CHF'

        elif bvr_type == '21':
            # Type: BVR in Euro
            bvr_struct = self._construct_bvr_in_chf(bvr_string)

            # We will set the currency , in this case it's allways EUR
            bvr_struct['currency'] = 'EUR'

        elif bvr_type == '31':
            # Type: postal BVR in Euro
            bvr_struct = self._construct_bvrplus_in_chf(bvr_string)

            # We will set the currency , in this case it's allways EUR
            bvr_struct['currency'] = 'EUR'

        elif bvr_type[0:1] == '<' and len(bvr_string) == 41:
            # Type: postal BVR in CHF
            bvr_struct = self._construct_bvr_postal_other_in_chf(bvr_string)

            # We will set the currency , in this case it's allways CHF
            bvr_struct['currency'] = 'CHF'

        else:
            raise except_orm(
                _('BVR Type error'),
                _('This kind of BVR is not supported at this time'))

        return bvr_struct
