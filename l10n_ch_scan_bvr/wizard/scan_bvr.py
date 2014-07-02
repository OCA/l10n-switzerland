# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi Vincent Renaville
#    Copyright 2013 Camptocamp SA
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

import pooler
import time

from openerp.osv import orm
from openerp.osv.orm import TransientModel, fields
from openerp.tools.translate import _


class scan_bvr(TransientModel):

    _name = "scan.bvr"
    _description = "BVR/ESR Scanning Wizard"

    _columns = {
        'journal_id': fields.many2one('account.journal',
                                      string="Invoice journal"),
        'bvr_string': fields.char(size=128,
                                  string='BVR String'),
        'partner_id': fields.many2one('res.partner',
                                      string="Partner"),
        'bank_account_id': fields.many2one('res.partner.bank',
                                           string="Partner Bank Account"),
        'state': fields.selection([
            ('new', 'New'),
            ('valid', 'valid'),
            ('need_extra_info', 'Need extra information'),
            ],
            'State'),
    }

    def _default_journal(self, cr, uid, context=None):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            ## We will get purchase journal linked with this company
            journal_ids = pool.get('account.journal').search(cr,
                                                             uid,
                                                             [('type', '=', 'purchase'),
                                                              ('company_id', '=', user.company_id.id)],
                                                             context=context)
            if len(journal_ids) == 1:
                return journal_ids[0]
            else:
                return False
        else:
            return False

    _defaults = {
        'state': 'new',
        'journal_id': _default_journal,
    }

    def _check_number(self, part_validation):
        nTab = [0, 9, 4, 6, 8, 2, 7, 1, 3, 5]
        resultnumber = 0
        for number in part_validation:
            resultnumber = nTab[(resultnumber + int(number) - 0) % 10]
        return (10 - resultnumber) % 10

    def _construct_bvrplus_in_chf(self, bvr_string):

            if len(bvr_string) != 43:
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in first part'))
            elif self._check_number(bvr_string[0:2]) != int(bvr_string[2]):
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in second part'))
            elif self._check_number(bvr_string[4:30]) != int(bvr_string[30]):
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in third part'))
            elif self._check_number(bvr_string[33:41]) != int(bvr_string[41]):
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in fourth part'))
            else:
                    bvr_struct = {'type': bvr_string[0:2],
                                  'amount': 0.0,
                                  'reference': bvr_string[4:31],
                                  'bvrnumber': bvr_string[4:10],
                                  'beneficiaire': self._create_bvr_account(
                                      bvr_string[33:42]
                                  ),
                                  'domain': '',
                                  'currency': ''
                                  }
                    return bvr_struct

    def _construct_bvr_in_chf(self, bvr_string):
            if len(bvr_string) != 53:
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in first part'))
            elif self._check_number(bvr_string[0:12]) != int(bvr_string[12]):
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in second part'))
            elif self._check_number(bvr_string[14:40]) != int(bvr_string[40]):
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in third part'))
            elif self._check_number(bvr_string[43:51]) != int(bvr_string[51]):
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in fourth part'))
            else:
                    bvr_struct = {'type': bvr_string[0:2],
                                  'amount': float(bvr_string[2:12])/100,
                                  'reference': bvr_string[14:41],
                                  'bvrnumber': bvr_string[14:20],
                                  'beneficiaire': self._create_bvr_account(
                                      bvr_string[43:52]
                                  ),
                                  'domain': '',
                                  'currency': ''
                                  }
                    return bvr_struct

    def _construct_bvr_postal_in_chf(self, bvr_string):
            if len(bvr_string) != 42:
                raise orm.except_orm(_('Validation Error'),
                                     _('BVR CheckSum Error in first part'))
            else:

                    bvr_struct = {'type': bvr_string[0:2],
                                  'amount': float(bvr_string[2:12])/100,
                                  'reference': bvr_string[14:30],
                                  'bvrnumber': '',
                                  'beneficiaire': self._create_bvr_account(
                                      bvr_string[32:41]
                                  ),
                                  'domain': '',
                                  'currency': ''
                                  }
                    return bvr_struct

    def _construct_bvr_postal_other_in_chf(self, bvr_string):
        ##
        if len(bvr_string) != 41:
            raise orm.except_orm(
                _('Validation Error'),
                _('BVR CheckSum Error in first part')
            )
        else:

                bvr_struct = {'type': bvr_string[0:2],
                              'amount': float(bvr_string[7:16])/100,
                              'reference': bvr_string[18:33],
                              'bvrnumber': '000000',
                              'beneficiaire': self._create_bvr_account(
                                  bvr_string[34:40]
                              ),
                              'domain': '',
                              'currency': ''
                              }
                return bvr_struct

    def _create_invoice_line(self, cr, uid, ids, data, context):
            invoice_line_ids = False
            pool = pooler.get_pool(cr.dbname)
            invoice_line_obj = pool.get('account.invoice.line')
            ## First we write partner_id
            self.write(cr, uid, ids, {'partner_id': data['partner_id']})
            ## We check that this partner have a default product
            accounts_data = pool.get('res.partner').read(
                cr, uid,
                data['partner_id'],
                ['supplier_invoice_default_product'],
                context=context
            )
            if accounts_data['supplier_invoice_default_product']:
                product_onchange_result = invoice_line_obj.product_id_change(
                    cr, uid, ids,
                    accounts_data['supplier_invoice_default_product'][0],
                    uom_id=False,
                    qty=0,
                    name='',
                    type='in_invoice',
                    partner_id=data['partner_id'],
                    fposition_id=False,
                    price_unit=False,
                    currency_id=False,
                    context=context,
                    company_id=None)
                ## We will check that the tax specified
                ## on the product is price include or amount is 0
                if product_onchange_result['value']['invoice_line_tax_id']:
                    taxes = pool.get('account.tax').browse(
                        cr, uid,
                        product_onchange_result['value']['invoice_line_tax_id']
                    )
                    for taxe in taxes:
                        if not taxe.price_include and taxe.amount != 0.0:
                            raise orm.except_orm(_('Error !'),
                                                 _('''The default product
                                                      in this partner have wrong taxes configuration'''))
                invoice_line_vals = {'product_id': accounts_data['supplier_invoice_default_product'][0],
                                     'account_id': product_onchange_result['value']['account_id'],
                                     'name': product_onchange_result['value']['name'],
                                     'uos_id': product_onchange_result['value']['uos_id'],
                                     'price_unit': data['bvr_struct']['amount'],
                                     'invoice_id': data['invoice_id'],
                                     'invoice_line_tax_id': [(6, 0, product_onchange_result['value']['invoice_line_tax_id'])]
                                     }
                invoice_line_ids = invoice_line_obj.create(
                    cr, uid, invoice_line_vals, context=context)
            return invoice_line_ids

    def _create_direct_invoice(self, cr, uid, ids, data, context):
        pool = pooler.get_pool(cr.dbname)
        ## We will call the function, that create invoice line
        account_invoice_obj = pool.get('account.invoice')
        account_invoice_tax_obj = pool.get('account.invoice.tax')
        if data['bank_account']:
            account_info = pool.get('res.partner.bank').browse(
                cr, uid, data['bank_account'],
                context=context
            )
        ## We will now search the currency_id
        #
        #
        currency_search = pool.get('res.currency').search(
            cr, uid,
            [('name',
              '=',
              data['bvr_struct']['currency'])],
            context=context
        )
        currency_id = pool.get('res.currency').browse(cr, uid,
                                                      currency_search[0],
                                                      context=context)
        ## Account Modification
        if data['bvr_struct']['domain'] == 'name':
            pool.get('res.partner.bank').write(
                cr, uid,
                data['bank_account'],
                {'post_number': data['bvr_struct']['beneficiaire']},
                context=context
            )
        else:
            pool.get('res.partner.bank').write(
                cr, uid,
                data['bank_account'],
                {'bvr_adherent_num': data['bvr_struct']['bvrnumber'],
                 'bvr_number': data['bvr_struct']['beneficiaire']},
                context=context
            )
        date_due = time.strftime('%Y-%m-%d')
        # We will now compute the due date and fixe the payment term
        payment_term_id = (account_info.partner_id.property_payment_term and
                           account_info.partner_id.property_payment_term.id or False)
        if payment_term_id:
            #We Calculate due_date
            res = pool.get('account.invoice').onchange_payment_term_date_invoice(
                cr, uid, [],
                payment_term_id,
                time.strftime('%Y-%m-%d')
            )
            date_due = res['value']['date_due']
        ##
        #
        curr_invoice = {'name': time.strftime('%Y-%m-%d'),
                        'partner_id': account_info.partner_id.id,
                        'account_id': account_info.partner_id.property_account_payable.id,
                        'date_due': date_due,
                        'date_invoice': time.strftime('%Y-%m-%d'),
                        'payment_term': payment_term_id,
                        'reference_type': 'bvr',
                        'reference':  data['bvr_struct']['reference'],
                        'amount_total':  data['bvr_struct']['amount'],
                        'check_total':  data['bvr_struct']['amount'],
                        'partner_bank_id': account_info.id,
                        'comment': '',
                        'currency_id': currency_id.id,
                        'journal_id': data['journal_id'],
                        'type': 'in_invoice',
                        }

        last_invoice = account_invoice_obj.create(cr, uid,
                                                  curr_invoice, context=context)
        data['invoice_id'] = last_invoice
        self._create_invoice_line(cr, uid, ids, data, context)
        ## Noew we create taxes lines
        computed_tax = account_invoice_tax_obj.compute(cr,
                                                       uid,
                                                       last_invoice,
                                                       context=context)
        inv = account_invoice_obj.browse(cr,
                                         uid,
                                         last_invoice,
                                         context=context)
        account_invoice_obj.check_tax_lines(cr,
                                            uid,
                                            inv,
                                            computed_tax,
                                            account_invoice_tax_obj)
        action = {'domain': "[('id','=', " + str(last_invoice) + ")]",
                  'name': 'Invoices',
                  'view_type': 'form',
                  'view_mode': 'form',
                  'res_model': 'account.invoice',
                  'view_id': False,
                  'context': "{'type':'out_invoice'}",
                  'type': 'ir.actions.act_window',
                  'res_id': last_invoice}
        return action

    def _create_bvr_account(self, account_unformated):
        account_formated = "%s-%s-%s" % (
            account_unformated[0:2],
            str(int(account_unformated[2:len(account_unformated)-1])),
            account_unformated[len(account_unformated)-1:len(account_unformated)]
        )
        return account_formated

    def _get_bvr_structurated(self, bvr_string):
        if bvr_string is not False:
            ## We will get the 2 frist digit of the BVr string in order
            ## to now the BVR type of this account
            bvr_type = bvr_string[0:2]
            if bvr_type == '01' and len(bvr_string) == 42:
                ## This BVr is the type of BVR in CHF
                # WE will call the function and Call
                bvr_struct = self._construct_bvr_postal_in_chf(bvr_string)
                ## We will test if the BVR have an Adherent Number if not we
                ## will make the search of the account base on
                ##his name non base on the BVR adherent number
                if (bvr_struct['bvrnumber'] == '000000'):
                    bvr_struct['domain'] = 'name'
                else:
                    bvr_struct['domain'] = 'bvr_adherent_num'
                ## We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            ##
            elif bvr_type == '01':
                ## This BVr is the type of BVR in CHF
                # WE will call the function and Call
                bvr_struct = self._construct_bvr_in_chf(bvr_string)
                ## We will test if the BVR have an Adherent Number if not
                ## we will make the search of the account base on
                ##his name non base on the BVR adherent number
                if (bvr_struct['bvrnumber'] == '000000'):
                    bvr_struct['domain'] = 'name'
                else:
                    bvr_struct['domain'] = 'bvr_adherent_num'
                ## We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            ##
            elif bvr_type == '03':
                ## It will be (At this time) the same work
                ## as for a standard BVR with 01 code
                bvr_struct = self._construct_bvr_postal_in_chf(bvr_string)
                ## We will test if the BVR have an Adherent Number
                ## if not we will make the search of the account base on
                ##his name non base on the BVR adherent number
                if (bvr_struct['bvrnumber'] == '000000'):
                    bvr_struct['domain'] = 'name'
                else:
                    bvr_struct['domain'] = 'bvr_adherent_num'
                ## We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            ##
            elif bvr_type == '04':
                ## It the BVR postal in CHF
                bvr_struct = self._construct_bvrplus_in_chf(bvr_string)
                ## We will test if the BVR have an Adherent Number
                ## if not we will make the search of the account base on
                ##his name non base on the BVR adherent number
                if (bvr_struct['bvrnumber'] == '000000'):
                    bvr_struct['domain'] = 'name'
                else:
                    bvr_struct['domain'] = 'bvr_adherent_num'
                ## We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            ##
            elif bvr_type == '21':
                ## It for a BVR in Euro
                bvr_struct = self._construct_bvr_in_chf(bvr_string)
                ## We will test if the BVR have an Adherent Number if
                ## not we will make the search of the account base on
                ##his name non base on the BVR adherent number
                if (bvr_struct['bvrnumber'] == '000000'):
                    bvr_struct['domain'] = 'name'
                else:
                    bvr_struct['domain'] = 'bvr_adherent_num'
                ## We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'EUR'
            ##
            elif bvr_type == '31':
                ## It the BVR postal in CHF
                bvr_struct = self._construct_bvrplus_in_chf(bvr_string)
                ## We will test if the BVR have an Adherent Number if not
                ## we will make the search of the account base on
                ##his name non base on the BVR adherent number
                if (bvr_struct['bvrnumber'] == '000000'):
                    bvr_struct['domain'] = 'name'
                else:
                    bvr_struct['domain'] = 'bvr_adherent_num'
                ## We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'EUR'

            elif bvr_type[0:1] == '<' and len(bvr_string) == 41:
                ## It the BVR postal in CHF
                bvr_struct = self._construct_bvr_postal_other_in_chf(bvr_string)
                ## We will test if the BVR have an Adherent Number
                ## if not we will make the search of the account base on
                ## his name non base on the BVR adherent number
                if (bvr_struct['bvrnumber'] == '000000'):
                    bvr_struct['domain'] = 'name'
                else:
                    bvr_struct['domain'] = 'bvr_adherent_num'
                ## We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            ##
            else:
                raise orm.except_orm(_('BVR Type error'),
                                     _('This kind of BVR is not supported at this time'))
            return bvr_struct

    def validate_bvr_string(self, cr, uid, ids, context):
        # We will now retrive result
        bvr_data = self.browse(cr, uid, ids, context)[0]
        # BVR Standrard
        #0100003949753>120000000000234478943216899+ 010001628>
        # BVR without BVr Reference
        #0100000229509>000000013052001000111870316+ 010618955>
        # BVR + In CHF
        #042>904370000000000000007078109+ 010037882>
        # BVR In euro
        #2100000440001>961116900000006600000009284+ 030001625>
        #<060001000313795> 110880150449186+ 43435>
        #<010001000165865> 951050156515104+ 43435>
        #<010001000060190> 052550152684006+ 43435>
        ##
        # Explode and check  the BVR Number and structurate it
        ##
        data = {}
        data['bvr_struct'] = self._get_bvr_structurated(
                                                        bvr_data.bvr_string
                                                        )
        ## We will now search the account linked with this BVR
        if data['bvr_struct']['domain'] == 'name':
            partner_bank_search = self.pool.get('res.partner.bank').search(
                                        cr,
                                        uid,
                                        [('acc_number',
                                          '=',
                                          data['bvr_struct']['beneficiaire']
                                        )],
                                        context=context)
        else:
            partner_bank_search = self.pool.get('res.partner.bank').search(
                                        cr,
                                        uid,
                                        [('bvr_adherent_num',
                                          '=',
                                          data['bvr_struct']['bvrnumber'])],
                                        context=context)
        ### We will need to know if we need to create invoice line
        if partner_bank_search:
            #we have found the account corresponding to the bvr_adhreent_number
            #so we can directly create the account
            #
            partner_bank_result = self.pool.get('res.partner.bank').browse(
                                            cr,
                                            uid,
                                            partner_bank_search[0],
                                            context=context
                                            )
            data['id'] = bvr_data.id
            data['partner_id'] = partner_bank_result.partner_id.id
            data['bank_account'] = partner_bank_result.id
            data['journal_id'] = bvr_data.journal_id.id
            action = self._create_direct_invoice(cr, uid,ids, data, context)
            return action
        elif bvr_data.bank_account_id:
            data['id'] = bvr_data.id
            data['partner_id'] = bvr_data.partner_id.id
            data['journal_id'] = bvr_data.journal_id.id
            data['bank_account'] = bvr_data.bank_account_id.id
            action = self._create_direct_invoice(cr, uid, ids, data, context)
            return action
        else:
            # we haven't found a valid bvr_adherent_number
            # we will need to create or update a bank account
            self.write(cr, uid, ids, {'state': 'need_extra_info'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'scan.bvr',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': bvr_data.id,
                'views': [(False, 'form')],
                'target': 'new',
            }
