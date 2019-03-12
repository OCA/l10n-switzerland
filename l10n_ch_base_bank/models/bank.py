# Copyright 2012-2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
from odoo import models, fields, api, _
from odoo.tools import mod10r
from odoo import exceptions

from odoo.addons.base_iban.models.res_partner_bank import normalize_iban


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
        iban = normalize_iban(iban)
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
        iban = normalize_iban(iban)
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
    country_code = fields.Char(
        string="Country code",
        related="country.code",
        readonly=True,
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
        # we sort by occurrence
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

    Statements:
    acc_type could be of 3 types:
        - postal
        - iban
        - bank

    if account has ccp and acc_type = 'postal' we dropped acc_number and
    compute it based on ccp, and partner

    if acc_number given in 'iban' format just transform to iban format, but no
    further modification on it, and acc_type = 'iban'

    if given bank is a postal (acc_type = 'postal') and ccp != bank.ccp it's
    mean that ccp in account is ccp of this partner in it's could be different
    acc_number in this case recomputed by as partner_name + ccp

    if given bank is a bank (acc_type = 'bank') then ccp in account should be
    the same as bank.ccp and acc_number recomputed

    if given ccp and no bank_id:
     - check if we already have banks with the same ccp in db, if found set
      this bank to account, update the rest
     - if no matches this mean this is a postal type, it has no bank, we
     set acc_number to this ccp number

    """
    _inherit = 'res.partner.bank'
    _compile_check_isr_add_num = re.compile('[0-9]*$')

    isr_adherent_num = fields.Char(
        string='Bank ISR adherent number', size=11,
        oldname='bvr_adherent_num',
        help="Your Bank adherent number to be printed "
             "in references of your ISR. "
             "This is not a postal account number."
    )
    acc_number = fields.Char(
        string='Account/IBAN Number'
    )
    ccp = fields.Char(
        string='CCP/CP-Konto',
        store=True
    )

    _sql_constraints = [
        ('isr_adherent_uniq', 'unique (isr_adherent_num, ccp)',
         'The ISR adherent number/ccp pair must be unique !'),
    ]

    @api.depends('acc_number')
    def _compute_acc_type(self):
        todo = self.env['res.partner.bank']
        for rec in self:
            if (rec.acc_number and
                    rec.is_swiss_postal_num(rec.acc_number)):
                rec.acc_type = 'postal'
                continue
            todo |= rec
        super(ResPartnerBank, todo)._compute_acc_type()

    @api.multi
    def get_account_number(self):
        """Retrieve the correct bank number to used based on
        account type
        """
        if self.ccp:
            return self.ccp
        else:
            return self.acc_number

    @api.constrains('isr_adherent_num')
    def _check_adherent_number(self):
        for p_bank in self:
            if not p_bank.isr_adherent_num:
                continue
            valid = self._compile_check_isr_add_num.match(
                p_bank.isr_adherent_num
            )
            if not valid:
                raise exceptions.ValidationError(
                    _('Your bank ISR adherent number must contain only '
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
    def _update_acc_name(self):
        """Check if number generated from ccp, if yes replace it on new """
        part_name = self.partner_id.name
        if not part_name and self.env.context.get('default_partner_id'):
            partner_id = self.env.context.get('default_partner_id')
            part_name = self.env['res.partner'].browse(partner_id)[0].name
        self.acc_number = self._compute_name_ccp(part_name, self.ccp)

    @api.multi
    def _compute_name_ccp(self, partner_name, ccp):
        """This method makes sure to generate a unique name"""
        if partner_name and ccp:
            acc_name = _("{}/CCP {}").format(partner_name, ccp)
        elif ccp:
            acc_name = _("CCP {}").format(ccp)
        else:
            return ''

        exist_count = self.env['res.partner.bank'].search_count(
            [('acc_number', '=like', acc_name)])
        # if acc_number not unique iterate on bank_accounts while not get
        # unique number
        if exist_count:
            name_exist = exist_count
            while name_exist:
                new_name = acc_name + " #{}".format(exist_count)
                name_exist = self.env['res.partner.bank'].search_count(
                    [('acc_number', '=', new_name)])
                exist_count += 1
            acc_name = new_name
        return acc_name

    @api.model
    def create(self, vals):
        """
        acc_number is mandatory for model, but in localization it could be not
        mandatory when we have ccp number, so we compute acc_number in onchange
        methods and check it here also
        """
        if not vals.get('acc_number') and vals.get('ccp'):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            vals['acc_number'] = self._compute_name_ccp(
                partner.name,
                vals['ccp']
            )
        return super().create(vals)

    @api.multi
    def _get_ch_bank_from_iban(self):
        """ Extract clearing number from iban to find the bank """
        if self.acc_type != 'iban':
            return False
        clearing = self._convert_iban_to_clearing(self.acc_number)
        return clearing and self.env['res.bank'].search(
            [('clearing', '=', clearing)], limit=1)

    @api.onchange('acc_number')
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
        if not self.acc_number:
            # if account number was flashed in UI
            self._update_acc_name()

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
    def onchange_ccp_set_acc_number(self):
        """If ccp changes and it's a postal bank update acc_number to ccp
        we don't want make acc_number as computed to have possibility set it
        manually and also avoid to shadow other logic on acc_number if exist
       """
        if self.acc_type == 'iban':
            return

        if self.ccp:
            if self.acc_type == 'postal':
                # flash bank if it was previously setup, also trigger acc_type
                # changing
                self.bank_id = ''
            self._update_acc_name()
        else:
            # flash bank if it was previously setup
            self.acc_number = ''

        if self.bank_id.is_swiss_post():
            self.acc_number = self.ccp
            return

        # try to find appropriate bank
        ccp = self.ccp
        if ccp and self.is_swiss_postal_num(ccp) and not self.bank_id.id:
            bank = (self.env['res.bank'].search([('ccp', '=', ccp)], limit=1)
                    or
                    self.env['res.bank'].search([('bic', '=', 'POFICHBEXXX')],
                                                limit=1))
            if not bank.is_swiss_post():
                self._update_acc_name()
            else:
                self.acc_number = self.ccp
            self.bank_id = bank

    @api.onchange('bank_id')
    def onchange_bank_set_acc_number(self):
        """ Track bank change to update acc_name if needed"""
        if not self.bank_id or self.acc_type == 'iban':
            return
        if self.bank_id.is_swiss_post():
            self.acc_number = self.ccp
        else:
            self._update_acc_name()

    @api.onchange('partner_id')
    def onchange_partner_set_acc_number(self):
        """
        when acc_number was computed automatically we call regeneration
        as partner name is part of acc_number
        """
        if self.acc_type == 'bank' and self.ccp:
            self._update_acc_name()
