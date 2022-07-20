# Copyright 2022 Openforce s.r.l.s
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
from odoo.tools.sql import column_exists, table_exists


@openupgrade.migrate()
def migrate(env, version):
    restore_ccp_bank_field(env)
    delete_previous_bank_view(env)


def restore_ccp_bank_field(env):
    """Restore value of `ccp` field from temporary column, to new field
    `l10n_ch_postal` added by backport v 12.0 feature
    """
    bank_tbl = env['res.bank']._table
    tmp_col = 'tmp_ccp'
    new_col = 'l10n_ch_postal'
    # Set old `ccp` field value to new `l10n_ch_postal` field in `res.bank`
    if table_exists(env.cr, bank_tbl) and \
            column_exists(env.cr, bank_tbl, tmp_col):
        env.cr.execute(
            """
            UPDATE {}
            SET {} = {}
            """.format(bank_tbl, new_col, tmp_col)
        )
        env.cr.execute(
            """
            ALTER TABLE {}
            DROP COLUMN {}
            """.format(bank_tbl, tmp_col)
        )


def delete_previous_bank_view(env):
    """Delete previous res partner bank view due to backport of module feature
    from v 12.0"""
    bbpbf_id = env.ref('l10n_ch_base_bank.add_ccp_on_res_partner_bank', False)
    if bbpbf_id:
        env.cr.execute("""
            DELETE FROM ir_ui_view WHERE id=%s;
        """, (bbpbf_id.id,))
