# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Switzerland - QR-IBAN",
    "version": "12.0.0.1.0",
    "author": "Odoo S.A, Camptocamp, Odoo Community Association (OCA)",
    "category": "Localization",
    "license": "LGPL-3",
    "depends": ["l10n_ch", "l10n_ch_fix_isr_reference"],
    "data": [
        "views/res_bank_views.xml",
        "views/swissqr_report.xml",
    ],
    "auto_install": True,
}
