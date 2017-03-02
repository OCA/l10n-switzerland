# -*- coding: utf-8 -*-
# Copyright 2016 Braintec AG (Kumar Aberer <kumar.aberer@braintec-group.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID


def update_bank_journals(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ajo = env['account.journal']
    journals = ajo.search([('type', '=', 'bank')])
    sct_id = env['ir.model.data'].xmlid_to_res_id(
        'l10n_ch_dta.dta_payment_method'
    )
    if journals:
        journals.write({
            'outbound_payment_method_ids': [(4, sct_id)],
        })
    return True
