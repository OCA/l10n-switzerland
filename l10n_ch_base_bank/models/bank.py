# -*- coding: utf-8 -*-
# Copyright 2012-2016 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
from odoo import models, fields, api, _
from odoo.tools import mod10r
from odoo import exceptions

from odoo.addons.base_iban.models.res_partner_bank import normalize_iban


class BankCommon(object):

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
        if not iban[:2] == 'CH':
            return False
        iban = normalize_iban(iban)
        part1 = iban[-9:-7]
        part2 = iban[-7:-1].lstrip('0')
        part3 = iban[-1:].lstrip('0')
        ccp = '{}-{}-{}'.format(part1, part2, part3)
        if not self._check_9_pos_postal_num(ccp):
            return False
        return ccp


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
            if not (self._check_9_pos_postal_num(bank.ccp) or
                    self._check_5_pos_postal_num(bank.ccp)):
                raise exceptions.ValidationError(
                    _('Please enter a correct postal number. '
                      '(01-23456-1 or 12345)')
                )
        return True

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
        compute="_compute_ccp",
        string='CCP/CP-Konto',
        store=True,
        readonly=True
    )

    @api.one
    @api.depends('acc_number')
    def _compute_acc_type(self):
        if (self.acc_number and
                (self._check_9_pos_postal_num(self.acc_number) or
                 self._check_5_pos_postal_num(self.acc_number))):
            self.acc_type = 'postal'
            return
        super(ResPartnerBank, self)._compute_acc_type()

    @api.one
    @api.depends('acc_type', 'bank_id.ccp')
    def _compute_ccp(self):
        """ Compute CCP
        It can be:
        - a postal account, we use acc_number
        - a postal account in iban format, we transform acc_number
        - a bank account with CCP on the bank, we use ccp of the bank
        - otherwise there is no CCP to use
        """
        if self.acc_type == 'postal':
            self.ccp = self.acc_number
        elif self.acc_type == 'iban' and self.bank_id.bic == 'POFICHBEXXX':
            self.ccp = self._convert_iban_to_ccp(self.acc_number.strip())
        elif self.bank_id.ccp:
            self.ccp = self.bank_id.ccp
        else:
            self.ccp = False

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

    @api.onchange('acc_number', 'acc_type')
    def onchange_set_swiss_post_bank(self):
        """ If acc_number is set to a postal number try to find the bank
        """
        if self.acc_type == 'postal':
            post = self.env['res.bank'].search([('bic', '=', 'POFICHBEXXX')])
            if post:
                self.bank_id = post

    @api.onchange('bank_id')
    def onchange_bank(self):
        """ If acc_number is empty and bank ccp is defined fill it """
        if not self.acc_number and self.bank_id.ccp:
            self.acc_number = 'Bank/CCP ' + self.bank_id.ccp

    _sql_constraints = [('bvr_adherent_uniq', 'unique (bvr_adherent_num)',
                         'The BVR adherent number must be unique !')]
