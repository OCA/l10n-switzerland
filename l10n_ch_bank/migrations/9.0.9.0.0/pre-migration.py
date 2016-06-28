# -*- coding: utf-8 -*-
# © 2015 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""
The banks have been created with dumb xml ids.
Change xml ids to keep track of those bank with
http://www.six-interbank-clearing.com/ (see README.rst for source)
"""


def migrate(cr, version):
    if not version:
        return

    query = (
        "UPDATE ir_model_data"
        "  SET name = 'bank_'||res_bank.clearing||_||res_bank.bank_branchid"
        "  FROM res_bank"
        "  WHERE module = 'l10n_ch_bank'"
        "    AND model = 'res.bank'"
        "    AND res_id = res_bank.id"
        "    AND res_bank.active = TRUE")
    cr.execute(query)
