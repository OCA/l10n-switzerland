# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Return Import PAIN CH",
    "summary": """
        This addon allows to import payment returns from PAIN CH.""",
    "version": "14.0.1.0.0",
    "development_status": "Mature",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA),Compassion CH",
    "website": "https://github.com/OCA/l10n-switzerland",
    "depends": [
        # OCA/account-payment
        "account_payment_return",
        "account_payment_return_import",
        "account_payment_return_import_iso20022",
        # OCA/bank-payment
        "account_payment_order",
    ],
    "data": ["data/payment.return.reason.csv"],
}
