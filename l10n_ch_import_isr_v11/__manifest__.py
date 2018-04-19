# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Switzerland - Import ISR v11',
    'version': '11.0.1.0.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'category': 'Localisation',
    'website': 'https://github.com/OCA/l10n-switzerland',
    'license': 'AGPL-3',
    'summary': 'Import of the ISR v11 files',
    'depends': [
        'l10n_ch_base_bank',
        'l10n_ch',
        'base_transaction_id',
    ],
    'data': [
        "wizard/isr_import_view.xml",
    ],
    'images': [],
    'demo': [],
}
