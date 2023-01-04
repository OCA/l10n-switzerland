# Copyright 2011 Camptocamp SA
# Copyright 2014 Olivier Jossen brain-tec AG
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Switzerland - Bank list",
    "summary": "Swiss banks names, addresses and BIC codes",
    "version": "16.0.1.0.0",
    "author": "Camptocamp, brain-tec AG, Odoo Community Association (OCA)",
    "category": "Localisation",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": ["l10n_ch_base_bank"],
    "data": [
        "data/res.bank.csv",
        "views/res_bank.xml",
    ],
    "post_init_hook": "post_init_hook",
}
