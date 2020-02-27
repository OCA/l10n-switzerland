from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Associate records with xml data
    export_sepa_dd = env['account.payment.method'].search([
        ('code', '=', 'sepa.ch.dd'),
        ('pain_version', '=', 'pain.008.001.02.ch.03')])
    if export_sepa_dd:
        openupgrade.add_xmlid(
            env.cr, 'l10n_ch_pain_direct_debit', 'export_sepa_dd',
            'account.payment.method', export_sepa_dd.id)
