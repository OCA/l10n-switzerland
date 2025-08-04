# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "eBill Postfinance",
    "summary": """Postfinance eBill integration""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["TDu"],
    "website": "https://github.com/OCA/l10n-switzerland",
    "depends": [
        "account",
        "account_invoice_export",
        "base_ebill_payment_contract",
        "l10n_ch",
        "sale",
    ],
    "external_dependencies": {
        "python": [
            "zeep",
            "ebilling_postfinance",
        ]
    },
    "data": [
        "data/ir_cron.xml",
        "data/transmit.method.xml",
        "data/mail_activity_type.xml",
        "security/ir.model.access.csv",
        "views/ebill_payment_contract.xml",
        "views/message_template.xml",
        "views/ebill_postfinance_service.xml",
        "views/ebill_postfinance_invoice_message.xml",
    ],
}
