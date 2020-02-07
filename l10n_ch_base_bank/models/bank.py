# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
from odoo import models, fields, api, _
from odoo.tools import mod10r
from odoo.exceptions import ValidationError

CH_POSTFINANCE_CLEARING = "09000"
CH_POST_BIC = 'POFICHBEXXX'


def validate_l10n_ch_postal(postal_acc_number):
    """Check if the string postal_acc_number is a valid postal account number,
    i.e. it only contains ciphers and is last cipher is the result of a
    recursive modulo 10 operation ran over the rest of it. Shorten form with -
    is also accepted.
    Raise a ValidationError if check fails
    """
    if not postal_acc_number:
        raise ValidationError(_("There is no postal account number."))
    if re.match('^[0-9]{2}-[0-9]{1,6}-[0-9]$', postal_acc_number):
        ref_subparts = postal_acc_number.split('-')
        postal_acc_number = (
            ref_subparts[0] + ref_subparts[1].rjust(6, '0') + ref_subparts[2]
        )

    if not re.match(r'\d{9}$', postal_acc_number or ''):
        msg = _("The postal does not match 9 digits position.")
        raise ValidationError(msg)

    acc_number_without_check = postal_acc_number[:-1]
    if not mod10r(acc_number_without_check) == postal_acc_number:
        raise ValidationError(_("The postal account number is not valid."))


def pretty_l10n_ch_postal(number):
    """format a postal account number or an ISR subscription number
    as per specifications with '-' separators.
    eg. 010000628 -> 01-162-8
    """
    if re.match('^[0-9]{2}-[0-9]{1,6}-[0-9]$', number or ''):
        return number
    currency_code = number[:2]
    middle_part = number[2:-1]
    trailing_cipher = number[-1]
    middle_part = re.sub('^0*', '', middle_part)
    return currency_code + '-' + middle_part + '-' + trailing_cipher


def _is_l10n_ch_postfinance_iban(iban):
    """Postfinance IBAN have format
    CHXX 0900 0XXX XXXX XXXX K
    Where 09000 is the clearing number
    """
    return (iban.startswith('CH')
            and iban[4:9] == CH_POSTFINANCE_CLEARING)


class Bank(models.Model):
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
        help="City of the bank",
    )
    country_code = fields.Char(
        string="Country code",
        related="country.code",
        readonly=True,
    )

    def is_swiss_post(self):
        return self.bic == CH_POST_BIC

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


class FutureResPartnerBank(models.Model):
    """This class contains features present in Odoo 13 in l10n_ch"""
    _inherit = 'res.partner.bank'  # pylint:disable=R7980

    l10n_ch_postal = fields.Char(oldname='ccp')

    # fields to configure ISR payment slip generation
    # (will be in standard in 13.0)
    l10n_ch_isr_subscription_chf = fields.Char(
        string='CHF ISR subscription number',
        help=(
            'The subscription number provided by the bank or Postfinance,'
            ' used to generate ISR in CHF. eg. 01-162-8'
        ),
        oldname="isr_adherent_num"
    )
    l10n_ch_isr_subscription_eur = fields.Char(
        string='EUR ISR subscription number',
        help=(
            "The subscription number provided by the bank or Postfinance,"
            " used to generate ISR in EUR. eg. 03-162-5"
        )
    )

    @api.model
    def _get_supported_account_types(self):
        result = super()._get_supported_account_types()
        result.append(('postal', _('Postal')))
        return result

    @api.model
    def retrieve_acc_type(self, acc_number):
        """ Overridden method enabling the recognition of swiss postal bank
        account numbers.
        """
        try:
            validate_l10n_ch_postal(acc_number)
            return 'postal'
        except ValidationError:
            return super().retrieve_acc_type(acc_number)

    @api.model
    def _retrieve_l10n_ch_postal(self, iban):
        """Reads a swiss postal account number from a an IBAN and returns it as
        a string. Returns None if no valid postal account number was found, or
        the given iban was not from Swiss Postfinance.

        CH09 0900 0000 1000 8060 7 -> 10-8060-7
        """
        # We can deduce postal account number only if
        # the financial institution is PostFinance
        if _is_l10n_ch_postfinance_iban(iban):
            # the IBAN corresponds to a swiss account
            try:
                validate_l10n_ch_postal(iban[-9:])
                return pretty_l10n_ch_postal(iban[-9:])
            except ValidationError:
                pass
        return None

    @api.model
    def create(self, vals):
        if vals.get('l10n_ch_postal'):
            try:
                validate_l10n_ch_postal(vals['l10n_ch_postal'])
                vals['l10n_ch_postal'] = pretty_l10n_ch_postal(
                    vals['l10n_ch_postal']
                )
            except ValidationError:
                pass
        return super().create(vals)

    def write(self, vals):
        if vals.get('l10n_ch_postal'):
            try:
                validate_l10n_ch_postal(vals['l10n_ch_postal'])
                vals['l10n_ch_postal'] = pretty_l10n_ch_postal(
                    vals['l10n_ch_postal']
                )
            except ValidationError:
                pass
        return super().write(vals)

    def _onchange_set_l10n_ch_postal(self):
        """OVERWRITE of onchange that copies bad things into l10n_ch_postal"""
        pass


class ResPartnerBank(models.Model):
    """Inherit res.partner.bank class in order to add swiss specific fields
    and state controls

    Statements:
    acc_type could be of 3 types:
        - postal
        - iban
        - bank

    if account has postal number and acc_type = 'postal' we dropped acc_number
    and compute it based on postal number, and partner

    if acc_number given in 'iban' format just transform to iban format, but no
    further modification on it, and acc_type = 'iban'

    it means that postal number in account is a number directly identifying
    the partner acc_number can contains the postal number

    if given bank account is 'bank' and l10n_ch_postal is set
    if given bank type is a 'bank' then postal number in account should be
    acc_number recomputed
    acc_number in this case recomputed by as partner_name + l10n_ch_postal

    """
    _inherit = 'res.partner.bank'

    @api.onchange('acc_number')
    def onchange_acc_number_set_swiss_bank(self):
        """ Deduce information from IBAN
        and set postal number when undefined
        Bank is defined as:
        - Found bank by clearing when using iban
        For Postal number it can be:
        - a postal account in iban format, we transform acc_number
        """
        if not self.acc_number:
            # if account number was flashed in UI
            self._update_acc_name()

        bank = self.bank_id
        postal = self.l10n_ch_postal
        if self.acc_type == 'iban':
            if not bank:
                bank = self._get_ch_bank_from_iban()
            postal = self._retrieve_l10n_ch_postal(
                self.sanitized_acc_number
            )
        elif self.acc_type == 'postal':
            postal = self.acc_number

        self.bank_id = bank
        self.l10n_ch_postal = postal

    @api.constrains(
        'l10n_ch_isr_subscription_chf',
        'l10n_ch_isr_subscription_eur'
    )
    def _check_subscription_num(self):
        for rec in self:
            for currency in ['chf', 'eur']:
                field_name = 'l10n_ch_isr_subscription_{}'.format(currency)
                if rec[field_name]:
                    validate_l10n_ch_postal(rec[field_name])
        return True

    @api.constrains('l10n_ch_postal')
    def _check_postal_num(self):
        """Validate postal number format"""
        for rec in self:
            if rec.l10n_ch_postal:
                validate_l10n_ch_postal(self.l10n_ch_postal)
        return True

    @api.multi
    def _update_acc_name(self):
        """Check if number generated from postal number, if yes replace it on
        new """
        part_name = self.partner_id.name
        if not part_name and self.env.context.get('default_partner_id'):
            partner_id = self.env.context.get('default_partner_id')
            part_name = self.env['res.partner'].browse(partner_id)[0].name
        self.acc_number = self._compute_name_from_postal_number(
            part_name, self.l10n_ch_postal)

    @api.model
    def _compute_name_from_postal_number(self, partner_name, postal_number):
        """This method makes sure to generate a unique name"""
        if partner_name and postal_number:
            acc_name = _("{}/Postal number {}").format(
                partner_name,
                postal_number
            )
        elif postal_number:
            acc_name = _("Postal number {}").format(postal_number)
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
        mandatory when we have postal number, so we compute acc_number in
        onchange methods and check it here also
        """
        if not vals.get('acc_number') and vals.get('l10n_ch_postal'):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            vals['acc_number'] = self._compute_name_from_postal_number(
                partner.name,
                vals['l10n_ch_postal']
            )
        return super().create(vals)

    @api.multi
    def _get_ch_bank_from_iban(self):
        """Extract clearing number from CH iban to find the bank"""
        if self.acc_type != 'iban' and self.acc_number[:2] != 'CH':
            return False
        clearing = self.sanitized_acc_number[4:9].lstrip('0')
        return clearing and self.env['res.bank'].search(
            [('clearing', '=', clearing)], limit=1)

    @api.onchange('l10n_ch_postal')
    def onchange_l10n_ch_postal_set_acc_number(self):
        """
        If postal number changes and it's a postal bank update acc_number to
        postal number we don't want make acc_number as computed to have
        possibility set it manually and also avoid to shadow other logic on
        acc_number if exist
        """
        if self.acc_type == 'iban':
            return

        if self.l10n_ch_postal:
            if self.acc_type == 'postal':
                # flash bank if it was previously setup, also trigger acc_type
                # changing
                self.bank_id = ''
            self._update_acc_name()
        else:
            # flash bank if it was previously setup
            self.acc_number = ''

        if self.bank_id.is_swiss_post():
            self.acc_number = self.l10n_ch_postal
            return

    @api.onchange('bank_id')
    def onchange_bank_set_acc_number(self):
        # Track bank change to update acc_name if needed
        if not self.bank_id or self.acc_type == 'iban':
            return
        if self.bank_id.is_swiss_post():
            self.acc_number = self.l10n_ch_postal
        else:
            self._update_acc_name()

    @api.onchange('partner_id')
    def onchange_partner_set_acc_number(self):
        # When acc_number was computed automatically we call regeneration
        # as partner name is part of acc_number
        if self.acc_type == 'bank' and self.l10n_ch_postal:
            self._update_acc_name()
