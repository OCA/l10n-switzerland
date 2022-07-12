# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Invoice report with payment',
    'version': '12.0.1.0.1',
    'author': 'Camptocamp, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'account',
        'l10n_ch_payment_slip',
        'l10n_ch',
        ],
    'data': [
        'data/report.xml',
        'views/res_config_settings.xml'
        ],
    'installable': True,
    'auto_install': False,
}
