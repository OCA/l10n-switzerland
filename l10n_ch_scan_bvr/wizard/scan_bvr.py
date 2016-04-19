# -*- coding: utf-8 -*-
# Author: Nicolas Bessi Vincent Renaville
# (c) 2013 Camptocamp SA
# (c) 2015 Alex Comba - Agile Business Group
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class ScanBvr(models.TransientModel):

    _name = "scan.bvr"
    _description = "BVR/ESR Scanning Wizard"

    journal_id = fields.Many2one(comodel_name='account.journal',
                                 string="Invoice journal",
                                 default='_default_journal')
    bvr_string = fields.Char(size=128, string='BVR String')
    partner_id = fields.Many2one(comodel_name='res.partner', string="Partner")
    bank_account_id = fields.Many2one(comodel_name='res.partner.bank',
                                      string="Partner Bank Account")
    state = fields.Selection(
        [('new', 'New'),
         ('valid', 'valid'),
         ('need_extra_info', 'Need extra information')],
        'State', default='new')

    @api.model
    def _default_journal(self):
        if self.env.user.company_id:
            # We will get purchase journal linked with this company
            journal_ids = self.env['account.journal'].search(
                [('type', '=', 'purchase'),
                 ('company_id', '=', self.env.user.company_id.id)],
            )
            if len(journal_ids) == 1:
                return journal_ids[0]
            else:
                return False
        else:
            return False

    def _check_number(self, part_validation):
        nTab = [0, 9, 4, 6, 8, 2, 7, 1, 3, 5]
        resultnumber = 0
        for number in part_validation:
            resultnumber = nTab[(resultnumber + int(number) - 0) % 10]
        return (10 - resultnumber) % 10

    def _construct_bvrplus_in_chf(self, bvr_string):
        if len(bvr_string) != 43:
            raise UserError(
                _('BVR CheckSum Error in first part')
            )
        elif self._check_number(bvr_string[0:2]) != int(bvr_string[2]):
            raise UserError(
                _('BVR CheckSum Error in second part')
            )
        elif self._check_number(bvr_string[4:30]) != int(bvr_string[30]):
            raise UserError(
                _('BVR CheckSum Error in third part')
            )
        elif self._check_number(bvr_string[33:41]) != int(bvr_string[41]):
            raise UserError(
                _('BVR CheckSum Error in fourth part')
            )
        else:
            bvr_struct = {
                'type': bvr_string[0:2],
                'amount': 0.0,
                'reference': bvr_string[4:31],
                'bvrnumber': bvr_string[4:10],
                'beneficiaire': self._create_bvr_account(bvr_string[33:42]),
                'domain': '',
                'currency': ''
            }
            return bvr_struct

    def _construct_bvr_in_chf(self, bvr_string):
        if len(bvr_string) != 53:
            raise UserError(
                _('BVR CheckSum Error in first part')
            )
        elif self._check_number(bvr_string[0:12]) != int(bvr_string[12]):
            raise UserError(
                _('BVR CheckSum Error in second part')
            )
        elif self._check_number(bvr_string[14:40]) != int(bvr_string[40]):
            raise UserError(
                _('BVR CheckSum Error in third part')
            )
        elif self._check_number(bvr_string[43:51]) != int(bvr_string[51]):
            raise UserError(
                _('BVR CheckSum Error in fourth part')
            )
        else:
            bvr_struct = {
                'type': bvr_string[0:2],
                'amount': float(bvr_string[2:12]) / 100,
                'reference': bvr_string[14:41],
                'bvrnumber': bvr_string[14:20],
                'beneficiaire': self._create_bvr_account(bvr_string[43:52]),
                'domain': '',
                'currency': ''
            }
            return bvr_struct

    def _construct_bvr_postal_in_chf(self, bvr_string):
        if len(bvr_string) != 42:
            raise UserError(
                _('BVR CheckSum Error in first part')
            )
        else:
            bvr_struct = {
                'type': bvr_string[0:2],
                'amount': float(bvr_string[2:12]) / 100,
                'reference': bvr_string[14:30],
                'bvrnumber': '000000',
                'beneficiaire': self._create_bvr_account(bvr_string[32:41]),
                'domain': '',
                'currency': ''
            }
            return bvr_struct

    def _construct_bvr_postal_other_in_chf(self, bvr_string):
        if len(bvr_string) != 41:
            raise UserError(
                _('BVR CheckSum Error in first part')
            )
        else:

            bvr_struct = {
                'type': bvr_string[0:2],
                'amount': float(bvr_string[7:16]) / 100,
                'reference': bvr_string[18:33],
                'bvrnumber': '000000',
                'beneficiaire': self._create_bvr_account(bvr_string[34:40]),
                'domain': '',
                'currency': ''
            }
            return bvr_struct

    @api.multi
    def _create_invoice_line(self, data):
        invoice_line = invoice_line_model = self.env['account.invoice.line']
        # First we write partner_id
        self.write({'partner_id': data['partner_id']})
        # We check that this partner have a default product
        partner = self.env['res.partner'].browse(data['partner_id'])
        if partner.supplier_invoice_default_product:
            prod = partner.supplier_invoice_default_product
            product_onchange_result = invoice_line_model.product_id_change(
                prod.id,
                uom_id=False,
                qty=0,
                name='',
                type='in_invoice',
                partner_id=partner.id,
                fposition_id=False,
                price_unit=False,
                currency_id=False,
                company_id=None
            )
            # We will check that the tax specified
            # on the product is price include or amount is 0
            if product_onchange_result['value']['invoice_line_tax_id']:
                taxes = self.env['account.tax'].browse(
                    product_onchange_result['value']['invoice_line_tax_id'])
                for taxe in taxes:
                    if not taxe.price_include and taxe.amount != 0.0:
                        raise UserError(
                            _('The default product in this partner has '
                              'wrong taxes configuration')
                        )
            account = product_onchange_result['value']['account_id']
            taxes = product_onchange_result['value']['invoice_line_tax_id']
            invoice_line_vals = {
                'product_id': prod.id,
                'account_id': account,
                'name': product_onchange_result['value']['name'],
                'uos_id': product_onchange_result['value']['uos_id'],
                'price_unit': data['bvr_struct']['amount'],
                'invoice_id': data['invoice_id'],
                'invoice_line_tax_id': [(6, 0, taxes)],
            }
            invoice_line = invoice_line_model.create(invoice_line_vals)
        return invoice_line

    @api.multi
    def _create_direct_invoice(self, data):
        # We will call the function, that create invoice line
        invoice_model = self.env['account.invoice']
        invoice_tax_model = self.env['account.invoice.tax']
        currency_model = self.env['res.currency']
        today = fields.Date.today()
        if data['bank_account']:
            account_info = self.env['res.partner.bank'].browse(
                data['bank_account'])
        # We will now search the currency_id
        currency = currency_model.search(
            [('name', '=', data['bvr_struct']['currency'])])
        date_due = today
        # We will now compute the due date and fixe the payment term
        payment_term_id = account_info.partner_id.property_payment_term.id
        if payment_term_id:
            # We Calculate due_date
            res = invoice_model.onchange_payment_term_date_invoice(
                payment_term_id, today)
            date_due = res['value']['date_due']

        invoice_vals = {
            'name': today,
            'partner_id': account_info.partner_id.id,
            'account_id': account_info.partner_id.property_account_payable.id,
            'date_due': date_due,
            'date_invoice': today,
            'payment_term': payment_term_id,
            'reference_type': 'bvr',
            'reference': data['bvr_struct']['reference'],
            'amount_total': data['bvr_struct']['amount'],
            'check_total': data['bvr_struct']['amount'],
            'partner_bank_id': account_info.id,
            'comment': '',
            'currency_id': currency.id,
            'journal_id': data['journal_id'],
            'type': 'in_invoice',
        }
        invoice = invoice_model.create(invoice_vals)
        data['invoice_id'] = invoice.id
        self._create_invoice_line(data)
        # Now we create taxes lines
        computed_tax = invoice_tax_model.compute(invoice)
        invoice.check_tax_lines(computed_tax)
        action = {
            'domain': "[('id','=', " + str(invoice.id) + ")]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': False,
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': invoice.id
        }
        return action

    def _create_bvr_account(self, account_unformated):
        acc_len = len(account_unformated)
        account_formated = "%s-%s-%s" % (
            account_unformated[0:2],
            str(int(account_unformated[2:acc_len - 1])),
            account_unformated[acc_len - 1:acc_len]
        )
        return account_formated

    def _get_bvr_structurated(self, bvr_string):
        if bvr_string is not False:
            # Get rid of leading and ending spaces of the BVR string
            bvr_string = bvr_string.strip()

            # We will get the 2 first digits of the BVR string in order
            # to know the BVR type of this account
            bvr_type = bvr_string[0:2]
            bvr_struct = {}
            if bvr_type == '01' and len(bvr_string) == 42:
                # This BVR is the type of BVR in CHF
                # WE will call the function and Call
                bvr_struct = self._construct_bvr_postal_in_chf(bvr_string)
                # We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            elif bvr_type == '01':
                # This BVR is the type of BVR in CHF
                # We will call the function and Call
                bvr_struct = self._construct_bvr_in_chf(bvr_string)
                # We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            elif bvr_type == '03':
                # It will be (At this time) the same work
                # as for a standard BVR with 01 code
                bvr_struct = self._construct_bvr_postal_in_chf(bvr_string)
                # We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            elif bvr_type == '04':
                # It the BVR postal in CHF
                bvr_struct = self._construct_bvrplus_in_chf(bvr_string)
                # We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            elif bvr_type == '21':
                # It for a BVR in Euro
                bvr_struct = self._construct_bvr_in_chf(bvr_string)
                # We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'EUR'
            ##
            elif bvr_type == '31':
                # It the BVR postal in CHF
                bvr_struct = self._construct_bvrplus_in_chf(bvr_string)
                # We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'EUR'

            elif bvr_type[0:1] == '<' and len(bvr_string) == 41:
                # It the BVR postal in CHF
                bvr_struct = self._construct_bvr_postal_other_in_chf(
                    bvr_string)
                # We will set the currency , in this case it's allways CHF
                bvr_struct['currency'] = 'CHF'
            else:
                raise UserError(_('This kind of BVR is not supported '
                                  'at this time'))
            # We will test if the BVR has an Adherent Number if not we
            # will make the search of the account base on
            # his name non base on the BVR adherent number
            if (bvr_struct['bvrnumber'] == '000000'):
                bvr_struct['domain'] = 'name'
            else:
                bvr_struct['domain'] = 'bvr_adherent_num'
            return bvr_struct

    @api.multi
    def validate_bvr_string(self):
        self.ensure_one()
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
        #
        # Explode and check  the BVR Number and structurate it
        #
        data = {}
        data['bvr_struct'] = self._get_bvr_structurated(self.bvr_string)
        partner_bank_model = self.env['res.partner.bank']
        partner_bank = False
        # We will now search the account linked with this BVR
        if data['bvr_struct']['domain'] == 'name':
            domain = [('acc_number', '=', data['bvr_struct']['beneficiaire'])]
            partners_bank = partner_bank_model.search(domain)
            partner_bank = len(partners_bank) == 1 and partners_bank[0]
        else:
            # A postal account that refers to a bank is uniquely identified
            # by (beneficiaire + bvrnumber), at least by beneficiaire
            domain = [('acc_number', '=', data['bvr_struct']['beneficiaire'])]
            partners_bank = partner_bank_model.search(domain)
            if len(partners_bank) == 1:
                if (
                        not partners_bank[0].bvr_adherent_num or
                        partners_bank[0].bvr_adherent_num ==
                        data['bvr_struct']['bvrnumber']):
                    partner_bank = partners_bank
            elif len(partners_bank) > 1:
                # We need to filter further by bvr_adherent_num
                partners_bank = partners_bank.filtered(
                    lambda r:
                    r.bvr_adherent_num == data['bvr_struct']['bvrnumber'])
                if len(partners_bank) > 1:
                    raise UserError(
                        _('There are more than one bank corresponding '
                          'to the current string.\n'
                          'Please check the banks configuration.'))
                partner_bank = partners_bank
        # We will need to know if we need to create invoice line
        if partner_bank:
            # We have found the account corresponding to the
            # bvr_adhreent_number
            # so we can directly create the account
            data['id'] = self.id
            data['partner_id'] = partner_bank.partner_id.id
            data['bank_account'] = partner_bank.id
            data['journal_id'] = self.journal_id.id
            action = self._create_direct_invoice(data)
            return action
        elif self.bank_account_id:
            data['id'] = self.id
            data['partner_id'] = self.partner_id.id
            data['journal_id'] = self.journal_id.id
            data['bank_account'] = self.bank_account_id.id
            action = self._create_direct_invoice(data)
            return action
        else:
            # we haven't found a valid bvr_adherent_number
            # we will need to create or update a bank account
            self.write({'state': 'need_extra_info'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'scan.bvr',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }
