# Author: Nicolas Bessi, Vincent Renaville
# Copyright 2012 Camptocamp SA
# Copyright 2015 Alex Comba - Agile Business Group
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Switzerland - Scan ESR/BVR to create invoices",
    "version": "11.0.1.0.0",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "category": "Generic Modules/Others",
    "website": "http://www.camptocamp.com",
    "license": "AGPL-3",
    "depends": [
        'base',
        'account',
        'l10n_ch_base_bank',
        'base_transaction_id'  # OCA/bank-statement-reconcile
    ],
    "data": [
        "security/security.xml",
        "wizard/scan_bvr_view.xml",
        "views/partner_view.xml",
    ],
    'installable': True,
}
