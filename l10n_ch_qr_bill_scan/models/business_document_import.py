# -*- coding: utf-8 -*-
# Copyright 2020-2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models

from odoo.addons.base_iban.models.res_partner_bank import (
    normalize_iban, pretty_iban
)


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def _hook_match_partner(
        self, partner_dict, chatter_msg, domain, partner_type_label
    ):
        # TODO search by iban
        return False

    @api.model
    def _match_partner_bank(
            self, partner, iban, bic, chatter_msg, create_if_not_found=False):
        '''Bank accounts with provided QR-IBAN
           should be found before Account/IBAN Number
        '''
        assert iban, 'iban is a required arg'
        assert partner, 'partner is a required arg'
        rpbo = self.env['res.partner.bank']
        partner = partner.commercial_partner_id
        iban = iban.replace(' ', '').upper()
        try:
            rpbo._validate_qr_iban(iban)
        except:
            chatter_msg.append(_(
                "IBAN <b>%s</b> is not valid, so it has been ignored.") % iban)
            return False
        company_id = self._context.get('force_company') or (
            self.env.user.company_id.id
        )
        qr_iban = pretty_iban(normalize_iban(iban))
        qr_iban_obj = rpbo.search([
            '|', ('company_id', '=', False),
            ('company_id', '=', company_id),
            ('l10n_ch_qr_iban', '=', qr_iban),
            ('partner_id', '=', partner.id),
            ])
        if qr_iban_obj:
            if len(qr_iban_obj) == 1:
                return qr_iban_obj
            else:
                chatter_msg.append(_(
                    "The analysis of the business document returned "
                    "<b>QR-IBAN %s</b> as bank account, but there are several "
                    "bank accounts in Odoo linked to partner <b>%s</b>."
                    "Please select propper bank account on Invoice.")
                    % (qr_iban, partner.display_name))
        else:
            bankaccount = super(BusinessDocumentImport, self)._match_partner_bank(
                partner, iban, bic, chatter_msg, create_if_not_found
            )
            return bankaccount

