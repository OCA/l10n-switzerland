# Copyright 2018 Camptocamp SA
# Copyright 2015 Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Switzerland - MIS reports',
    'summary': 'Specific MIS reports for switzerland localization',
    'version': '11.0.1.1.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'category': 'Localization',
    'website': 'https://github.com/OCA/l10n-switzerland',
    'license': 'AGPL-3',
    'depends': [
        'l10n_ch',
        'mis_builder_budget',
        'l10n_ch_account_tags',
    ],
    'data': [
        'data/mis_report_style.xml',
        'data/mis_report.xml',
        'data/mis_report_kpi.xml',
    ],
    'installable': False,
}
