# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "eBill Paynet",
    "summary": """
        Paynet platform bridge implementation""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp SA,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-switzerland",
    "depends": [
        "account",
        "account_invoice_export",
        "base_ebill_payment_contract",
        "l10n_ch_base_bank",
        "l10n_ch_qriban",
        "queue_job",
        "sale",
        "delivery",
    ],
    "external_dependencies": {"python": ["zeep"]},
    "data": [
        "data/transmit.method.xml",
        "data/ir_cron.xml",
        "data/mail_activity_type.xml",
        "security/ir.model.access.csv",
        "views/ebill_payment_contract.xml",
        "views/message_template.xml",
        "views/paynet_service.xml",
        "views/paynet_invoice_message.xml",
    ],
    "demo": [],
}
