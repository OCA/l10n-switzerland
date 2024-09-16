# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "Switzerland - PAIN Direct Debit",
    "summary": "Generate ISO 20022 direct debits",
    "version": "14.0.1.0.0",
    "category": "Finance",
    "author": "Akretion,Camptocamp,Compassion,Odoo Community Association(OCA)",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "maintainers": ["alexis-via", "ecino"],
    "depends": ["account_banking_sepa_direct_debit", "l10n_ch_pain_base"],
    "external_dependencies": {"python": ["openupgradelib"]},
    "data": [
        "data/account_payment_method.xml",
    ],
    "auto_install": False,
    "installable": True,
}
