# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models


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

    _inherit = "res.partner.bank"

    def is_isr_issuer(self):
        """Supplier will provide ISR/QRR reference numbers in two cases:

        - postal account number starting by 01 or 03
        - QR-IBAN
        """
        # acc_type can be bank for isrb
        if self.acc_type in ["bank", "postal"] and self.l10n_ch_postal:
            return self.l10n_ch_postal[:2] in ["01", "03"]
        return self.acc_type == "iban" and self._is_qr_iban()

    def _get_ch_bank_from_iban(self):
        """Extract clearing number from CH iban to find the bank"""
        if self.acc_type != "iban" and self.acc_number[:2] != "CH":
            return False
        clearing = self.sanitized_acc_number[4:9].lstrip("0")
        return clearing and self.env["res.bank"].search(
            [("clearing", "=", clearing)], limit=1
        )

    @api.onchange("acc_number", "acc_type")
    def _onchange_acc_number_set_swiss_bank(self):
        """Deduce information from IBAN

        Bank is defined as:
        - Found bank by clearing when using iban
        """
        bank = self.bank_id
        if self.acc_type == "iban":
            bank = self._get_ch_bank_from_iban()
        self.bank_id = bank

    @api.onchange("l10n_ch_postal")
    def _onchange_postal_set_acc_number(self):
        """Set acc_number from postal field"""
        if self.acc_type != "iban" and self.l10n_ch_postal:
            self._update_acc_number()

    @api.onchange("partner_id")
    def onchange_partner_set_acc_number(self):
        # When acc_number was computed automatically we call regeneration
        # as partner name is part of acc_number
        # This is only required for ISR subscription numbers
        if self.l10n_ch_postal and self.l10n_ch_postal[:2] in ["01", "03"]:
            self._update_acc_number()

    def _update_acc_number(self):
        """Compute value for field acc_number
        based on an postal account or ISR subscription number"""
        part_name = self.partner_id.name
        if not part_name and self.env.context.get("default_partner_id"):
            partner_id = self.env.context.get("default_partner_id")
            part_name = self.env["res.partner"].browse(partner_id)[0].name
        self.acc_number = self._compute_name_from_postal_number(
            part_name, self.l10n_ch_postal
        )

    @api.model
    def _compute_name_from_postal_number(self, partner_name, postal_number):
        """This method makes sure to generate a unique name"""
        if postal_number and postal_number[:2] in ["01", "03"]:
            if partner_name:
                acc_name = _("ISR {} {}").format(postal_number, partner_name)
            else:
                acc_name = _("ISR {}").format(postal_number)
        else:
            return postal_number

        exist_count = self.env["res.partner.bank"].search_count(
            [("acc_number", "=like", acc_name)]
        )
        # if acc_number not unique iterate on bank_accounts while not get
        # unique number
        if exist_count:
            name_exist = exist_count
            while name_exist:
                new_name = acc_name + " #{}".format(exist_count)
                name_exist = self.env["res.partner.bank"].search_count(
                    [("acc_number", "=", new_name)]
                )
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
        if not vals.get("acc_number") and vals.get("l10n_ch_postal"):
            partner = self.env["res.partner"].browse(vals.get("partner_id"))
            vals["acc_number"] = self._compute_name_from_postal_number(
                partner.name, vals["l10n_ch_postal"]
            )
        return super().create(vals)
