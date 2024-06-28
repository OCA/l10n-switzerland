# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Switzerland - No Amount QR-bill",
    "summary": "Allow to print QR bill without amount",
    "version": "17.0.1.0.0",
    "development_status": "Alpha",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-switzerland",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["grindtildeath"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["l10n_ch"],
    "data": ["report/swissqr_no_amount_report.xml"],
    "assets": {
        "web.report_assets_common": [
            "l10n_ch_qr_no_amount/static/src/scss/report_swissqr_no_amount.scss",
        ],
    },
}
