# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
from openerp import models, fields, api, _
from openerp.tools import mod10r
from openerp import exceptions

from openerp.addons.base_iban import base_iban


class BankCommon(object):

    def is_swiss_postal_num(self, number):
        return (self._check_9_pos_postal_num(number) or
                self._check_5_pos_postal_num(number))

    def _check_9_pos_postal_num(self, number):
        """
        Predicate that checks if a postal number
        is in format xx-xxxxxx-x is correct,
        return true if it matches the pattern
        and if check sum mod10 is ok

        :param number: postal number to validate
        :returns: True if is it a 9 len postal account
        :rtype: bool
        """
        pattern = r'^[0-9]{2}-[0-9]{1,6}-[0-9]$'
        if not re.search(pattern, number):
            return False
        nums = number.split('-')
        prefix = nums[0]
        num = nums[1].rjust(6, '0')
        checksum = nums[2]
        expected_checksum = mod10r(prefix + num)[-1]
        return expected_checksum == checksum

    def _check_5_pos_postal_num(self, number):
        """
        Predicate that checks if a postal number
        is in format xxxxx is correct,
        return true if it matches the pattern
        and if check sum mod10 is ok

        :param number: postal number to validate
        :returns: True if is it a 5 len postal account
        :rtype: bool
        """
        pattern = r'^[0-9]{1,5}$'
        if not re.search(pattern, number):
            return False
        return True

    def _convert_iban_to_ccp(self, iban):
        """
        Convert a Postfinance IBAN into an old postal number
        """
        iban = base_iban.normalize_iban(iban)
        if not iban[:2].upper() == 'CH':
            return False
        part1 = iban[-9:-7]
        part2 = iban[-7:-1].lstrip('0')
        part3 = iban[-1:].lstrip('0')
        ccp = '{}-{}-{}'.format(part1, part2, part3)
        if not self._check_9_pos_postal_num(ccp):
            return False
        return ccp

    def _convert_iban_to_clearing(self, iban):
        """
        Convert a Swiss Iban to a clearing
        """
        iban = base_iban.normalize_iban(iban)
        if not iban[:2].upper() == 'CH':
            return False
        clearing = iban[4:9].lstrip('0')
        return clearing


class Bank(models.Model, BankCommon):
    """Inherit res.bank class in order to add swiss specific field"""
    _inherit = 'res.bank'

    code = fields.Char(
        string='Code',
        help='Internal reference'
    )
    clearing = fields.Char(
        string='Clearing number',
        help='Swiss unique bank identifier also used in IBAN number'
    )
    city = fields.Char(
        string='City',
        help="City of the bank"
    )
    ccp = fields.Char(
        string='CCP/CP-Konto',
        size=11,
        help="CCP/CP-Konto of the bank"
    )

    @api.constrains('ccp')
    def _check_postal_num(self):
        """Validate postal number format"""
        for bank in self:
            if not bank.ccp:
                continue
            if not self.is_swiss_postal_num(bank.ccp):
                raise exceptions.ValidationError(
                    _('Please enter a correct postal number. '
                      '(01-23456-1 or 12345)')
                )
        return True

    @api.multi
    def is_swiss_post(self):
        return self.bic == 'POFICHBEXXX'

    @api.multi
    def name_get(self):
        """Format displayed name"""
        res = []
        cols = ('bic', 'name', 'street', 'city')
        for bank in self:
            vals = (bank[x] for x in cols if bank[x])
            res.append((bank.id, ' - '.join(vals)))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        """Extends to look on bank code, bic, name, street and city"""
        if args is None:
            args = []
        ids = []
        cols = ('code', 'bic', 'name', 'street', 'city')
        if name:
            for val in name.split(' '):
                for col in cols:
                    tmp_ids = self.search(
                        [(col, 'ilike', val)] + args,
                        limit=limit
                    )
                    if tmp_ids:
                        ids += tmp_ids.ids
                        break
        else:
            ids = self.search(
                args,
                limit=limit
                ).ids
        # we sort by occurence
        to_ret_ids = list(set(ids))
        to_ret_ids = sorted(
            to_ret_ids,
            key=lambda x: ids.count(x),
            reverse=True
        )
        return self.browse(to_ret_ids).name_get()


class ResPartnerBank(models.Model, BankCommon):
    """Inherit res.partner.bank class in order to add swiss specific fields
    and state controls

    """
    _inherit = 'res.partner.bank'
    _compile_check_bvr_add_num = re.compile('[0-9]*$')

    bvr_adherent_num = fields.Char(
        string='Bank BVR/ESR adherent number', size=11,
        help="Your Bank adherent number to be printed "
             "in references of your BVR/ESR. "
             "This is not a postal account number."
        )
    acc_number = fields.Char(
        string='Account/IBAN Number'
    )
    ccp = fields.Char(
        string='CCP/CP-Konto',
        store=True
    )

    @api.one
    @api.depends('acc_number')
    def _compute_acc_type(self):
        if (self.acc_number and
                self.is_swiss_postal_num(self.acc_number)):
            self.acc_type = 'postal'
            return
        super(ResPartnerBank, self)._compute_acc_type()

    @api.multi
    def get_account_number(self):
        """Retrieve the correct bank number to used based on
        account type
        """
        if self.ccp:
            return self.ccp
        else:
            return self.acc_number

    @api.constrains('bvr_adherent_num')
    def _check_adherent_number(self):
        for p_bank in self:
            if not p_bank.bvr_adherent_num:
                continue
            valid = self._compile_check_bvr_add_num.match(
                p_bank.bvr_adherent_num
            )
            if not valid:
                raise exceptions.ValidationError(
                    _('Your bank BVR/ESR adherent number must contain only '
                      'digits!\nPlease check your company bank account.')
                )
        return True

    @api.constrains('ccp')
    def _check_postal_num(self):
        """Validate postal number format"""
        for bank in self:
            if not bank.ccp:
                continue
            if not self.is_swiss_postal_num(bank.ccp):
                raise exceptions.ValidationError(
                    _('Please enter a correct postal number. '
                      '(01-23456-1 or 12345)')
                )
        return True

    @api.multi
    def _get_acc_name(self):
        """ Return an account name for a bank account
        to use with a ccp for BVR.
        This method make sure to generate a unique name
        """
        part_name = self.partner_id.name
        if part_name:
            acc_name = _("Bank/CCP {}").format(self.partner_id.name)
        else:
            acc_name = _("Bank/CCP Undefined")

        exist_count = self.env['res.partner.bank'].search_count(
            [('acc_number', '=like', acc_name)])
        if exist_count:
            name_exist = exist_count
            while name_exist:
                new_name = acc_name + " ({})".format(exist_count)
                name_exist = self.env['res.partner.bank'].search_count(
                    [('acc_number', '=', new_name)])
                exist_count += 1
            acc_name = new_name
        return acc_name

    @api.multi
    def _get_ch_bank_from_iban(self):
        """ Extract clearing number from iban to find the bank """
        if self.acc_type != 'iban':
            return False
        clearing = self._convert_iban_to_clearing(self.acc_number)
        return clearing and self.env['res.bank'].search(
            [('clearing', '=', clearing)], limit=1)

    @api.onchange('acc_number', 'acc_type')
    def onchange_acc_number_set_swiss_bank(self):
        """ Set the bank when possible
        and set ccp when undefined
        Bank is defined as:
        - Found bank with CCP matching Bank CCP
        - Swiss post when CCP is no matching a Bank CCP
        - Found bank by clearing when using iban
        For CCP it can be:
        - a postal account, we copy acc_number
        - a postal account in iban format, we transform acc_number
        - a bank account with CCP on the bank, we use ccp of the bank
        - otherwise there is no CCP to use
        """
        bank = self.bank_id
        ccp = False
        if self.acc_type == 'postal':
            ccp = self.acc_number
            # Try to find a matching bank to the ccp entered in acc_number
            # Overwrite existing bank if there is a match
            bank = (
                self.env['res.bank'].search([('ccp', '=', ccp)], limit=1) or
                bank or
                self.env['res.bank'].search([('bic', '=', 'POFICHBEXXX')],
                                            limit=1))
            if not bank.is_swiss_post():
                self.acc_number = self._get_acc_name()
        elif self.acc_type == 'iban':
            if not bank:
                bank = self._get_ch_bank_from_iban()
            if bank:
                if bank.is_swiss_post():
                    ccp = self._convert_iban_to_ccp(self.acc_number.strip())
                else:
                    ccp = bank.ccp
        elif self.bank_id.ccp:
            ccp = self.bank_id.ccp
        self.bank_id = bank
        if not self.ccp:
            self.ccp = ccp

    @api.onchange('ccp')
    def onchange_ccp_set_empty_acc_number(self):
        """ If acc_number is empty and bank ccp is defined fill it """
        if self.bank_id:
            if not self.acc_number and self.ccp:
                if self.bank_id.is_swiss_post():
                    self.acc_number = self.ccp
                else:
                    self.acc_number = self._get_acc_name()
            return

        ccp = self.ccp
        if ccp and self.is_swiss_postal_num(ccp):
            bank = (
                self.env['res.bank'].search([('ccp', '=', ccp)], limit=1) or
                self.env['res.bank'].search([('bic', '=', 'POFICHBEXXX')],
                                            limit=1))
            if not self.acc_number:
                if not bank.is_swiss_post():
                    self.acc_number = self._get_acc_name()
                else:
                    self.acc_number = self.ccp
            self.bank_id = bank

    @api.onchange('bank_id')
    def onchange_bank_set_acc_number(self):
        """ If acc_number is empty and bank ccp is defined fill it """
        if not self.bank_id:
            return
        if self.bank_id.is_swiss_post():
            if not self.acc_number:
                self.acc_number = self.ccp
            elif not self.ccp and self.is_swiss_postal_num(self.acc_number):
                self.ccp = self.acc_number
        else:
            if not self.acc_number and self.ccp:
                self.acc_number = self._get_acc_name()
            elif self.acc_number and self.is_swiss_postal_num(self.acc_number):
                self.ccp = self.acc_number
                self.acc_number = self._get_acc_name()

    @api.onchange('partner_id')
    def onchange_partner_set_acc_number(self):
        if self.acc_type == 'bank' and self.ccp:
            if 'Bank/CCP' in self.acc_number:
                self.acc_number = self._get_acc_name()

    _sql_constraints = [('bvr_adherent_uniq', 'unique (bvr_adherent_num, ccp)',
                         'The BVR adherent number/ccp pair must be unique !')]
