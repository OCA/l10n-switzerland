# Copyright 2025 Openindustry
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Currency Rate Update: Federal Tax Administration",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "summary": """
        Update exchange rates using https://www.backend-rates.bazg.admin.ch/api/xmldaily
    """,
    "category": "Financial Management/Configuration",
    "company": "https://openindustry.it",
    "author": "Openindustry.it,Odoo Community Association (OCA)",
    "maintainers": ["andreampiovesana"],
    "support": "andrea.m.piovesana@gmail.com",
    "website": "https://github.com/OCA/l10n-switzerland",
    "depends": [
        "currency_rate_update",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "currency": "EUR",
}
