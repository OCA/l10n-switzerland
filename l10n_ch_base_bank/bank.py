# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Financial contributors: Hasa SA, Open Net SA,
#                            Prisme Solutions Informatique SA, Quod SA
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
from openerp import models, fields, api, _
from openerp.tools import mod10r
from openerp import exceptions


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


class Bank(models.Model, BankCommon):
    """Inherit res.bank class in order to add swiss specific field"""
    _inherit = 'res.bank'

    code = fields.Char(
        string='Code',
        size=64,
        help='Internal reference'
    )
    clearing = fields.Char(
        string='Clearing number',
        size=64,
        help='Swiss unique bank identifier also used in IBAN number'
    )
    city = fields.Char(
        string='City',
        help="City of the bank"
    )
    ccp = fields.Char(
        string='CCP/CP-Konto',
        size=64,
        help="CCP/CP-Konto of the bank"
    )

    @api.constrains('ccp')
    def _check_ccp_duplication(self):
        """Ensure validity of input"""
        res_part_bank_model = self.env['res.partner.bank']
        for bank in self:
            part_bank_accs = res_part_bank_model.search(
                [('bank', '=', bank.id)]
            )

            if part_bank_accs:
                part_bank_accs._check_ccp_duplication()
        return True

    @api.constrains('ccp')
    def _check_postal_num(self):
        """Validate postal number format"""
        for bank in self:
            if not bank.ccp:
                continue
            if not (self._check_9_pos_postal_num(bank.ccp)):
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
        string='CCP/CP-Konto',
        related='bank.ccp',
        store=True,
        readonly=True
    )

    @api.multi
    def get_account_number(self):
        """Retrieve the correct bank number to used based on
        account type
        """
        if self.state not in ('bv', 'bvr'):
            return self.acc_number
        if self.bank and self.bank.ccp:
            return self.bank.ccp
        else:
            return self.acc_number

    @api.constrains('bvr_adherent_num')
    def _check_adherent_number(self):
        for p_bank in self:
            if not self.bvr_adherent_num:
                continue
            valid = self._compile_check_bvr_add_num.match(
                self.bvr_adherent_num
            )
            if not valid:
                raise exceptions.ValidationError(
                    'Your bank BVR/ESR adherent number must contain only '
                    'digits!\nPlease check your company '
                )
        return True

    @api.constrains('acc_number')
    def _check_postal_num(self):
        """Validate postal number format
        """
        for p_bank in self:
            if p_bank.state not in ('bv', 'bvr'):
                continue
            acc = p_bank.get_account_number()
            if not acc:
                continue
            if not (
                    self._check_9_pos_postal_num(acc) or
                    self._check_5_pos_postal_num(acc)):
                raise exceptions.ValidationError(
                    _('Please enter a correct postal number. '
                      '(01-23456-1 or 12345)')
                )

    @api.constrains('acc_number', 'bank')
    def _check_ccp_duplication(self):
        """Ensure that there is not a CCP/CP-Konto in bank and res partner bank
        at same time

        """
        for p_bank in self:
            if p_bank.state not in ('bv', 'bvr'):
                continue
            bank_ccp = p_bank.bank.ccp if p_bank.bank else False
            if not bank_ccp:
                continue
            part_bank_check = (
                self._check_5_pos_postal_num(p_bank.acc_number) or
                self._check_9_pos_postal_num(p_bank.acc_number)
            )
            bank_check = (
                self._check_5_pos_postal_num(p_bank.bank.ccp) or
                self._check_9_pos_postal_num(p_bank.bank.ccp)
            )
            if part_bank_check and bank_check:
                raise exceptions.ValidationError(
                    _('You can not enter a CCP/CP-Konto both on '
                      'the bank and on an account '
                      'of type BV/ES, BVR/ESR')
                )

    _sql_constraints = [('bvr_adherent_uniq', 'unique (bvr_adherent_num)',
                         'The BVR adherent number must be unique !')]
