# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Set the res.bank records as noupdate

    When importing .csv files we can't mark them as noupdate in the manifest,
    so we do it here.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    records = env["ir.model.data"].search(
        [
            ("module", "=", "l10n_ch_bank"),
            ("model", "=", "res.bank"),
        ]
    )
    records.write({"noupdate": True})
