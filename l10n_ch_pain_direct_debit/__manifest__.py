# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "Switzerland - PAIN Direct Debit",
    "summary": "Generate ISO 20022 direct debits",
    "version": "11.0.1.0.0",
    "category": "Finance",
    "author": "Akretion,Camptocamp,Compassion,Odoo Community Association(OCA)",
    'website': 'http://www.compassion.ch,http://www.braintec-group.com',
    "license": "AGPL-3",
    "depends": [
        "account_banking_sepa_direct_debit",
        "l10n_ch_pain_base"
    ],
    'data': [
        'data/payment_type.xml',
        'data/export_filename_sequence.xml',
        'views/account_payment_line_view.xml',
        'views/account_payment_mode_view.xml',
        'views/account_payment_order_view.xml',
        'views/bank_payment_line_view.xml'
    ],
    'demo': [
        'demo/dd_demo.yml'
    ],
    'auto_install': False,
    'installable': True,
}
