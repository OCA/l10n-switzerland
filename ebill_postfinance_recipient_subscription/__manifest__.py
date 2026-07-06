{
    "name": "E-Bill PostFinance Recipient Subscription",
    "version": "18.0.1.0.0",
    "category": "Finance",
    "summary": "Module for e-bill recipient subscription "
    "via PostFinance website workflow.",
    "author": "Compassion CH,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": ["ebill_postfinance", "website", "base"],
    "data": [
        "data/ir_config_parameter_data.xml",
        "data/ir_cron_data.xml",
        "views/ebill_recipient_subscription_workflow.xml",
    ],
    "installable": True,
}
