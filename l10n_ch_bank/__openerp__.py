# -*- coding: utf-8 -*-
# © 2011-2014 Nicolas Bessi (Camptocamp SA)
# © 2014 Olivier Jossen brain-tec AG
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Switzerland - Bank list',
    'version': '9.0.1.0.0',
    'author': "Camptocamp, brain-tec AG,Odoo Community Association (OCA)",
    'category': 'Localisation',
    'website': 'http://www.camptocamp.com',
    'license': 'AGPL-3',
    'summary': 'Banks names, addresses and BIC codes',
    'depends': ['l10n_ch',
                'l10n_ch_base_bank',
                ],
    'data': ['data/bank.xml',
             'views/res_config.xml'
             ],
    'images': [],
    'demo': [],
    'auto_install': False,
    'installable': True,
    'application': True,
}
