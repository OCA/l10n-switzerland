# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright Camptocamp SA
#    Financial contributors: Hasa SA, Open Net SA,
#                            Prisme Solutions Informatique SA, Quod SA
#    Ported to v8.0 by Agile Business Group <http://www.agilebg.com>
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
import time
import re
import base64
import unicode2ascii

from openerp.exceptions import except_orm
from openerp import models, fields, api, _
from openerp.tools import mod10r

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

TRANS = [(u'é', 'e'),
         (u'è', 'e'),
         (u'à', 'a'),
         (u'ê', 'e'),
         (u'î', 'i'),
         (u'ï', 'i'),
         (u'â', 'a'),
         (u'ä', 'a'),
         (u'ö', 'o'),
         (u'ü', 'u')]


def _u2a(text):
    """Tries to convert unicode charactere to asci equivalence"""
    if not text:
        return ""
    txt = ""
    for c in text:
        if ord(c) < 128:
            txt += c
        elif c in unicode2ascii.EXTRA_LATIN_NAMES:
            txt += unicode2ascii.EXTRA_LATIN_NAMES[c]
        elif c in unicode2ascii.UNI2ASCII_CONVERSIONS:
            txt += unicode2ascii.UNI2ASCII_CONVERSIONS[c]
        elif c in unicode2ascii.EXTRA_CHARACTERS:
            txt += unicode2ascii.EXTRA_CHARACTERS[c]
        elif c in unicode2ascii.FG_HACKS:
            txt += unicode2ascii.FG_HACKS[c]
        else:
            txt += "_"
    return txt


def tr(string_in):
    try:
        string_in = string_in.decode('utf-8')
    except:
        # If exception => then just take the string as is
        pass
    for k in TRANS:
        string_in = string_in.replace(k[0], k[1])
    try:
        res = string_in.encode('ascii', 'replace')
    except:
        res = string_in
    return res


class record(object):
    """Abstract class that provides common
    knowledge for any kind of post/bank account

    """

    def __init__(self, global_context_dict, pool, pline):
        self.pool = pool
        self.pline = pline
        for i in global_context_dict:
            global_context_dict[i] = (global_context_dict[i] and
                                      tr(global_context_dict[i]))
        self.fields = []
        self.global_values = global_context_dict
        self.validate_global_context_dict()
        self.pre = {
            'padding': '',
            'seg_num1': '01',
            'seg_num2': '02',
            'seg_num3': '03',
            'seg_num4': '04',
            'seg_num5': '05',
            'flag': '0',
            'zero5': '00000'
        }
        self.post = {'date_value_hdr': '000000', 'type_paiement': '0'}
        self.init_local_context()

    def init_local_context(self):
        """Instanciate a fields list, field = (name,size)
        and update a local_values dict.

        """
        raise NotImplementedError('Init not implemented')

    def validate_global_context_dict(self):
        """Validate values of global context parameter"""
        raise NotImplementedError('Check not implemented')

    def generate(self):
        """Generate formatted fields data in DTA format
        for a given account

        """
        res = ''
        for field in self.fields:
            if field[0] in self.pre:
                value = self.pre[field[0]]
            elif field[0] in self.global_values:
                value = self.global_values[field[0]]
            elif field[0] in self.post:
                value = self.post[field[0]]
            else:
                pass
            try:
                res = res + c_ljust(value, field[1])
            except:
                pass
        return res


class postal_record(record):
    """Class that propose common
    knowledge for all postal account type

    """
    def __init__(self, global_context_dict, pool, pline):
        super(postal_record, self).__init__(global_context_dict, pool, pline)
        self.is_9_pos_adherent = False

    def validate_global_context_dict(self):
        """Ensure postal record is valid"""
        # if adherent bvr number is a 9 pos number
        # add 0 to fill 2nd part plus remove '-'
        # exemple: 12-567-C becomes 12000567C
        if _is_9_pos_bvr_adherent(self.global_values['partner_bvr']):
            parts = self.global_values['partner_bvr'].split('-')
            parts[1] = parts[1].rjust(6, '0')
            self.global_values['partner_bvr'] = ''.join(parts)
            self.is_9_pos_adherent = True
        # add 4*0 to bvr adherent number with 5 pos
        # exemple: 12345 becomes 000012345
        elif len(self.global_values['partner_bvr']) == 5:
            val = self.global_values['partner_bvr'].rjust(9, '0')
            self.global_values['partner_bvr'] = val
        else:
            raise except_orm(
                _('Error'),
                _('Wrong postal number format.\n'
                  'It must be 12-123456-9 or 12345 format')
            )


class record_gt826(postal_record):
    """ BVR record implementation"""

    def init_local_context(self):
        """Define field of BVR records"""
        self.fields = [
            ('seg_num1', 2),
            # header
            ('date_value_hdr', 6),
            ('partner_bank_clearing', 12),
            ('zero5', 5),
            ('creation_date', 6),
            ('comp_bank_clearing', 7),
            ('uid', 5),
            ('sequence', 5),
            ('genre_trans', 3),
            ('type_paiement', 1),
            ('flag', 1),
            # seg1
            ('comp_dta', 5),
            ('number', 11),
            ('comp_bank_iban', 24),
            ('date_value', 6),
            ('currency', 3),
            ('amount_to_pay', 12),
            ('padding', 14),
            # seg2
            ('seg_num2', 2),
            ('comp_name', 20),
            ('comp_street', 20),
            ('comp_zip', 10),
            ('comp_city', 10),
            ('comp_country', 20),
            ('padding', 46),
            # seg3
            ('seg_num3', 2),
            ('partner_bvr', 12),  # Numero d'adherent bvr
            ('partner_name', 20),
            ('partner_street', 20),
            ('partner_zip', 10),
            ('partner_city', 10),
            ('partner_country', 20),
            ('reference', 27),  # Communication structuree
            ('padding', 2),  # Cle de controle
            ('padding', 5)
        ]
        self.pre.update({
            'date_value_hdr': self.global_values['date_value'],
            'date_value': '',
            'partner_bank_clearing': '',
            'partner_cpt_benef': '',
            'genre_trans': '826',
            'conv_cours': '',
            'option_id_bank': 'D',
            'partner_bvr': '/C/' + self.global_values['partner_bvr'],
            'ref2': '',
            'ref3': '',
            'format': '0',
        })

    def validate_global_context_dict(self):
        """Validate BVR record values"""
        super(record_gt826, self).validate_global_context_dict()
        if not self.global_values['reference']:
            raise except_orm(
                _('Error'),
                _('You must provide a BVR reference'
                  'number \n for the line: %s') % self.pline.name
            )
        ref = self.global_values['reference'].replace(' ', '')
        self.global_values['reference'] = ref
        if self.is_9_pos_adherent:
            if len(ref) > 27:
                raise except_orm(
                    _('Error'),
                    _('BVR reference number is not valid \n'
                      'for the line: %s. \n'
                      'Reference is too long.') % self.pline.name
                )
            # do a mod10 check
            if mod10r(ref[:-1]) != ref:
                raise except_orm(
                    _('Error'),
                    _('BVR reference number is not valid \n'
                      'for the line: %s. \n'
                      'Mod10 check failed') % self.pline.name
                )
            # fill reference with 0
            self.global_values['reference'] = ref.rjust(27, '0')
        else:
            # reference of BVR adherent with 5 positions number
            # have 15 positions references
            if len(ref) > 15:
                raise except_orm(
                    _('Error'),
                    _('BVR reference number is not valid \n'
                      'for the line: %s. \n Reference is too long '
                      'for this type of beneficiary.') % self.pline.name
                )
            # complete 15 first digit with 0 on left and complete 27 digits
            # with trailing spaces
            # exemple: 123456 becomes 00000000012345____________
            adjust = ref.rjust(15, '0').ljust(27, ' ')
            self.global_values['reference'] = adjust

        if not self.global_values['partner_bvr']:
            raise except_orm(
                _('Error'),
                _('You must provide a BVR number\n'
                  'for the bank account: %s'
                  'on line: %s') % (self.pline.bank_id.get_account_number(),
                                    self.pline.name)
            )


class record_gt827(postal_record):
    """
    Swiss internal (bvpost and bvbank) record implemetation
    """
    def validate_global_context_dict(self):
        """Validate record values"""
        super(record_gt827, self).validate_global_context_dict()
        if not self.global_values['partner_bank_number']:
            raise except_orm(
                _('Error'),
                _('You must provide a bank number \n'
                  'for the partner bank: %s\n on line: %s') %
                (self.pline.bank_id.get_account_number(), self.pline.name)
            )
        if not self.global_values['partner_bank_clearing']:
            raise except_orm(
                _('Error'),
                _('You must provide a Clearing Number\n'
                  'for the partner bank: %s\n on line %s') %
                (self.pline.bank_id.get_account_number(), self.pline.name)
            )
        frm = '/C/%s' % self.global_values['partner_bank_number']
        self.global_values['partner_bank_number'] = frm

    def init_local_context(self):
        """Define fields values"""
        self.fields = [
            ('seg_num1', 2),
            # header
            ('date_value_hdr', 6),
            ('partner_bank_clearing', 12),
            ('zero5', 5),
            ('creation_date', 6),
            ('comp_bank_clearing', 7),
            ('uid', 5),
            ('sequence', 5),
            ('genre_trans', 3),
            ('type_paiement', 1),
            ('flag', 1),
            # seg1
            ('comp_dta', 5),
            ('number', 11),
            ('comp_bank_iban', 24),
            ('date_value', 6),
            ('currency', 3),
            ('amount_to_pay', 12),
            ('padding', 14),
            # seg2
            ('seg_num2', 2),
            ('comp_name', 20),
            ('comp_street', 20),
            ('comp_zip', 10),
            ('comp_city', 10),
            ('comp_country', 20),
            ('padding', 46),
            # seg3
            ('seg_num3', 2),
            ('partner_bank_number', 30),
            ('partner_name', 24),
            ('partner_street', 24),
            ('partner_zip', 12),
            ('partner_city', 12),
            ('partner_country', 24),
            # seg4
            ('seg_num4', 2),
            ('reference', 112),
            ('padding', 14),
            # seg5
            # ('padding',128)
        ]

        self.pre.update({
            'date_value_hdr': self.global_values['date_value'],
            'date_value': '',
            'partner_cpt_benef': '',
            'type_paiement': '0',
            'genre_trans': '827',
            'conv_cours': '',
            'option_id_bank': 'D',
            'ref2': '',
            'ref3': '',
            'format': '0'
        })


class record_gt836(record):
    """Implements iban record"""

    def validate_global_context_dict(self):
        """Validate iban values"""

        def _compute_bank_ident(values):
            res = '%s %s %s %s %s' % (values['partner_bank_name'],
                                      values['partner_bank_street'],
                                      values['partner_bank_zip'],
                                      values['partner_bank_city'],
                                      values['partner_bank_country'])
            return res

        part = self.pline.partner_id
        p_country = '%s-' % part.country_id.code if part.country_id else ''
        self.global_values['partner_country'] = p_country
        co_addr = self.pline.order_id.company_id
        country = '%s-' % co_addr.country_id.code if co_addr.country_id else ''
        self.global_values['comp_country'] = country

        if not self.global_values['partner_bank_iban']:
            raise except_orm(
                _('Error'),
                _('No IBAN defined \n for the bank account: %s\n'
                  'on line: %s') % (self.pline.bank_id.get_account_number(),
                                    self.pline.name)
            )
        # Bank code is swift (BIC address)
        if self.global_values['partner_bank_code']:
            self.global_values['option_id_bank'] = 'A'
            code = self.global_values['partner_bank_code']
            self.global_values['partner_bank_ident'] = code
        elif self.global_values['partner_bank_city']:
            self.global_values['option_id_bank'] = 'D'
            self.global_values['partner_bank_ident'] = _compute_bank_ident(
                self.global_values
            )
        else:
            raise except_orm(
                _('Error'),
                _('You must provide the bank city '
                  'or the bic code for the partner bank:\n %s\n on line: %s') %
                (self.pline.bank_id.get_account_number(), self.pline.name)
            )

    def init_local_context(self):
        """Define iban fields"""
        self.fields = [
            ('seg_num1', 2),
            # header
            ('date_value_hdr', 6),
            ('partner_bank_clearing', 12),
            ('zero5', 5),
            ('creation_date', 6),
            ('comp_bank_clearing', 7),
            ('uid', 5),
            ('sequence', 5),
            ('genre_trans', 3),
            ('type_paiement', 1),
            ('flag', 1),
            # seg1
            ('comp_dta', 5),
            ('number', 11),
            ('comp_bank_iban', 24),
            ('date_value', 6),
            ('currency', 3),
            ('amount_to_pay', 15),
            ('padding', 11),
            # seg2
            ('seg_num2', 2),
            ('conv_cours', 12),
            ('comp_name', 35),
            ('comp_street', 35),
            ('comp_country', 3),
            ('comp_zip', 10),
            ('comp_city', 22),
            ('padding', 9),
            # seg3
            ('seg_num3', 2),
            ('option_id_bank', 1),
            ('partner_bank_ident', 70),
            ('partner_bank_iban', 34),
            ('padding', 21),
            # seg4
            ('seg_num4', 2),
            ('partner_name', 35),
            ('partner_street', 35),
            ('partner_country', 3),
            ('partner_zip', 10),
            ('partner_city', 22),
            ('padding', 21),
            # seg5
            ('seg_num5', 2),
            ('option_motif', 1),
            ('reference', 105),
            ('format', 1),
            ('padding', 19)
        ]
        self.pre.update({
            'partner_bank_clearing': '',
            'partner_cpt_benef': '',
            'type_paiement': '0',
            'genre_trans': '836',
            'conv_cours': '',
            'reference': self.global_values['reference'],
            'ref2': '',
            'ref3': '',
            'format': '2'
        })
        self.post.update({'option_motif': 'U'})


class record_gt890(record):
    """Implements Total Record of DTA file
    if behaves like a account payment order

    """
    def init_local_context(self):
        """Initialise fields"""
        self.fields = [
            ('seg_num1', 2),
            # header
            ('date_value_hdr', 6),
            ('partner_bank_clearing', 12),
            ('zero5', 5),
            ('creation_date', 6),
            ('comp_bank_clearing', 7),
            ('uid', 5),
            ('sequence', 5),
            ('genre_trans', 3),
            ('type_paiement', 1),
            ('flag', 1),
            # total
            ('amount_total', 16),
            ('padding', 59)
        ]
        self.pre.update({'partner_bank_clearing': '', 'partner_cpt_benef': '',
                         'company_bank_clearing': '', 'genre_trans': '890'})

    def validate_global_context_dict(self):
        return


def c_ljust(s, size):
    """
    check before calling ljust
    """
    s = s or ''
    if len(s) > size:
        s = s[:size]
    s = s.decode('utf-8').encode('latin1', 'replace').ljust(size)
    return s


def _is_9_pos_bvr_adherent(adherent_num):
    """
    from a bvr adherent number,
    return true if
    """
    pattern = r'[0-9]{2}-[0-9]{1,6}-[0-9]'
    return re.search(pattern, adherent_num)


class DTAFileGenerator(models.TransientModel):
    _name = "create.dta.wizard"

    @api.model
    def _initialize_elec_context(self, data):
        elec_context = {}
        payment_obj = self.env['payment.order']
        payment = payment_obj.browse(data['id'])
        elec_context['uid'] = str(self.env.user)
        elec_context['creation_date'] = fields.Date.today()
        if not payment.mode:
            raise except_orm(
                _('Error'),
                _('No payment mode')
            )
        bank = payment.mode.bank_id
        if not bank:
            raise except_orm(
                _('Error'),
                _('No bank account for the company.')
            )
        if not bank.bank:
            raise except_orm(
                _('Error'),
                _('You must set a bank '
                  'for the bank account with number %s' %
                  bank.acc_number or '')
            )
        elec_context['comp_bank_name'] = bank.bank.name
        elec_context['comp_bank_clearing'] = bank.bank.clearing
        if not elec_context['comp_bank_clearing']:
            raise except_orm(
                _('Error'),
                _('You must provide a Clearing Number '
                  'for the bank %s.' % bank.bank.name)
            )
        company = payment.company_id
        co_addr = company.partner_id
        co = co_addr.country_id.name if co_addr.country_id else ''
        elec_context['comp_country'] = co
        elec_context['comp_street'] = co_addr.street or ''
        elec_context['comp_zip'] = co_addr.zip
        elec_context['comp_city'] = co_addr.city
        elec_context['comp_name'] = co_addr.name
        # Used by Mamuth payment systems
        elec_context['comp_dta'] = bank.dta_code or ''
        # Iban and account number are the same field and
        # depends only on the type of account
        acc = bank.acc_number or ''
        elec_context['comp_bank_iban'] = acc.replace(' ', '') or ''
        elec_context['comp_bank_number'] = acc
        if not elec_context['comp_bank_iban']:
            raise except_orm(
                _('Error'),
                _('No IBAN for the company bank account.')
            )
        return elec_context

    @api.model
    def _set_bank_data(self, pline, elec_context, seq):
        elec_context['partner_bank_city'] = pline.bank_id.bank.city or False
        elec_context['partner_bank_street'] = pline.bank_id.bank.street or ''
        elec_context['partner_bank_zip'] = pline.bank_id.bank.zip or ''
        bank = pline.bank_id.bank
        b_country = bank.country.name if bank.country else ''
        elec_context['partner_bank_country'] = b_country

        elec_context['partner_bank_code'] = pline.bank_id.bank_bic
        elec_context['reference'] = pline.move_line_id.ref
        # Add support for owner of the account if exists..
        p_name = pline.partner_id.name if pline.partner_id else ''
        elec_context['partner_name'] = p_name
        if pline.partner_id:
            part = pline.partner_id
            elec_context['partner_street'] = part.street
            elec_context['partner_city'] = part.city
            elec_context['partner_zip'] = part.zip

            # If iban => country=country code for space reason
            p_country = part.country_id.name if part.country_id else ''
            elec_context['partner_country'] = p_country
        else:
            raise except_orm(
                _('Error'),
                _('No address defined \n for the partner: %s on line') %
                (pline.partner_id.name, pline.name)
            )

    @api.model
    def _process_payment_lines(self, data, pline, elec_context, seq):
        if not pline.bank_id:
            raise except_orm(
                _('Error'),
                _('No bank account defined\n on line: %s') % pline.name
            )
        if not pline.bank_id.bank:
                raise except_orm(
                    _('Error'),
                    _('No bank defined for the bank account: %s\n'
                      'on the partner: %s\n on line: %s') %
                    (pline.bank_id.state,
                     pline.partner_id.name,
                     pline.name)
                )
        elec_context['sequence'] = str(seq).rjust(5).replace(' ', '0')
        am_to_pay = str(pline.amount_currency).replace('.', ',')
        elec_context['amount_to_pay'] = am_to_pay
        elec_context['number'] = pline.name
        elec_context['currency'] = pline.currency.name
        elec_context['partner_bank_name'] = pline.bank_id.bank_name or False
        clearing = pline.bank_id.bank.clearing or False
        elec_context['partner_bank_clearing'] = clearing
        if not elec_context['partner_bank_name']:
            raise except_orm(
                _('Error'),
                _('No bank name defined\n for the bank account: %s\n'
                  'on the partner: %s\n on line: %s') % (pline.bank_id.state,
                                                         pline.partner_id.name,
                                                         pline.name)
            )
        elec_context['partner_bank_iban'] = (
            pline.bank_id.get_account_number() or
            False
        )
        number = pline.bank_id.get_account_number() or ''
        number = number.replace('.', '').replace('-', '') or False
        elec_context['partner_bank_number'] = number
        elec_context['partner_bvr'] = ''
        if pline.bank_id.state in ('bv', 'bvr'):
            part = pline.bank_id.get_account_number() or ''
            elec_context['partner_bvr'] = part
        self._set_bank_data(pline, elec_context, seq)
        if pline.order_id.date_scheduled:
            date_value = fields.Datetime.from_string(
                pline.order_id.date_scheduled)
        elif pline.date:
            date_value = fields.Datetime.from_string(pline.date)
        else:
            date_value = fields.Datetime.now()
        elec_context['date_value'] = date_value
        return elec_context

    @api.model
    def _create_dta(self, data):
        """Generate DTA file"""
        elec_context = self._initialize_elec_context(data)
        dta = ''
        payment_obj = self.env['payment.order']
        attachment_obj = self.env['ir.attachment']
        res_partner_bank_obj = self.env['res.partner.bank']
        payment = payment_obj.browse(data['id'])
        seq = 1
        amount_tot = 0
        amount_currency_tot = 0

        for pline in payment.line_ids:
            elec_context = self._process_payment_lines(
                data, pline,
                elec_context, seq
            )
            # si compte iban -> iban (836)
            # si payment structure  -> bvr (826)
            # si non -> (827)
            elec_pay = pline.bank_id.state  # Bank type
            part = pline.partner_id
            country_code = part.country_id.code if part.country_id else False
            if elec_pay in ['iban', 'bank']:
                # If iban => country=country code for space reason
                record_type = record_gt836
            elif country_code and country_code != 'CH':
                record_type = record_gt836
            elif elec_pay == 'bvr':
                record_type = record_gt826
            elif elec_pay == 'bv':
                record_type = record_gt827
            else:
                name = res_partner_bank_obj.name_get(
                    self.env.cr,
                    self.env.user,
                    [pline.bank_id.id],
                    self._context
                )
                name = name[0][1]
                raise except_orm(
                    _('Error'),
                    _('The Bank type %s of the bank account: %s '
                      'is not supported') %
                    (elec_pay, name)
                )

            dta_line = record_type(elec_context, self.pool, pline).generate()

            dta = dta + dta_line
            amount_tot += pline.amount
            amount_currency_tot += pline.amount_currency
            seq += 1

        # segment total
        amount = str(amount_currency_tot).replace('.', ',')
        elec_context['amount_total'] = amount
        sequence = str(seq).rjust(5).replace(' ', '0')
        elec_context['sequence'] = sequence
        if dta:
            dta = dta + record_gt890(elec_context, self.pool, False).generate()
        dta_data = _u2a(dta)
        dta_data = base64.encodestring(dta)
        payment_obj.set_done([data['id']])
        dta_file_name = 'DTA%s.txt' % time.strftime(
            DEFAULT_SERVER_DATETIME_FORMAT, time.gmtime())
        dta_dict = {
            'name': dta_file_name,
            'datas': dta_data,
            'datas_fname': dta_file_name,
            'res_model': 'payment.order',
            'res_id': data['id']
        }
        attachment_obj.create(dta_dict)
        return dta_data

    @api.multi
    def create_dta(self):
        context = self._context
        data = {}
        active_ids = context.get('active_ids', [])
        active_id = context.get('active_id', [])
        data['form'] = {}
        data['ids'] = active_ids
        data['id'] = active_id
        dta_file = self._create_dta(data)
        return dta_file
