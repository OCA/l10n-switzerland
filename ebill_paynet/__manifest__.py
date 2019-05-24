# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Ebill Paynet",
    "summary": """
        Paynet platform bridge implementation""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp SA,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-switzerland",
    "depends": ["account", "base_ebill_payment_contract", "l10n_ch_base_bank"],
    "external_dependencies": {"python": ["zeep"]},
    "data": [
        "data/transmit.method.xml",
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "views/ebill_payment_contract.xml",
        "views/paynet_service.xml",
        "views/paynet_invoice_message.xml",
    ],
    "demo": [],
}
