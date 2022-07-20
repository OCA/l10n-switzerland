# Copyright 2022 Openforce s.r.l.s
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
from odoo.tools.sql import column_exists, table_exists


@openupgrade.migrate()
def migrate(env, version):
    save_ccp_bank_field(env)


def save_ccp_bank_field(env):
    """Save value of `ccp` field in a temporary column, because backport v 12.0
    feature remove this field and substitute it with `l10n_ch_postal`
    """
    bank_tbl = env['res.bank']._table
    partner_bank_tbl = env['res.partner.bank']._table
    old_col = 'ccp'
    tmp_col = 'tmp_ccp'
    new_part_bank_col = 'l10n_ch_postal'
    # Set old `ccp` field value to tmp `tmp_ccp` field in `res.bank`
    if table_exists(env.cr, bank_tbl) and \
            column_exists(env.cr, bank_tbl, old_col):
        env.cr.execute(
            """
            ALTER TABLE {}
            ADD COLUMN {} varchar
            """.format(bank_tbl, tmp_col)
        )
        env.cr.execute(
            """
            UPDATE {}
            SET {} = {}
            """.format(bank_tbl, tmp_col, old_col)
        )
    # Set old `ccp` field value to tmp `tmp_ccp` field in `res.partner.bank`
    if table_exists(env.cr, partner_bank_tbl) and \
            column_exists(env.cr, partner_bank_tbl, old_col):
        env.cr.execute(
            """
            ALTER TABLE {}
            RENAME COLUMN {} TO {}
            """.format(partner_bank_tbl, old_col, new_part_bank_col)
        )
