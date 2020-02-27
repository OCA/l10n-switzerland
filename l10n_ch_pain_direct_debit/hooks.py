import logging

_logger = logging.getLogger(__name__)

try:
    from openupgradelib import openupgrade
    can_migrate = True
except ImportError:
    can_migrate = False
    _logger.warning("Install openupgradelib to migrate from v10.")


def pre_init_hook(cr):
    cr.execute("""
        SELECT id
        FROM account_payment_method
        WHERE code = 'sepa.ch.dd' AND pain_version = 'pain.008.001.02.ch.03'
    """)
    res_id = cr.fetchone()
    if can_migrate and res_id:
        _logger.info("Associating module data with database record.")
        openupgrade.add_xmlid(
            cr, 'l10n_ch_pain_direct_debit', 'export_sepa_dd',
            'account.payment.method', res_id[0])
