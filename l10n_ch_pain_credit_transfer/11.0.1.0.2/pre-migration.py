from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Associate records with xml data
    sepa_ct_ch = env['account.payment.method'].search([
        ('code', '=', 'sepa_credit_transfer'),
        ('pain_version', '=', 'pain.001.001.03.ch.02')])
    if sepa_ct_ch:
        openupgrade.add_xmlid(
            env.cr, 'l10n_ch_pain_credit_transfer', 'export_sepa_ct_ch',
            'account.payment.method', sepa_ct_ch.id)
