# -*- coding: utf-8 -*-
# © 2017 Emanuel Cino <ecino@compassion.ch>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

# New v9 module dependencies
to_install = [
    'account_payment_order',
    'account_payment_mode',
    'account_banking_pain_base',
    'account_banking_sepa_direct_debit',
]


def install_new_modules(cr):
    sql = """
    UPDATE ir_module_module
    SET state='to install'
    WHERE name in %s AND state='uninstalled'
    """ % (tuple(to_install),)
    openupgrade.logged_query(cr, sql)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    install_new_modules(env.cr)
    # Remove invalid data
    openupgrade.logged_query(env.cr, """
        DELETE FROM ir_model_data
        WHERE model = 'payment.mode.type' AND module = 'l10n_ch_lsv_dd';
    """)
