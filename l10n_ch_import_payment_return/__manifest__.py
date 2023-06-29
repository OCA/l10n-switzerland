# Copyright 2023 Compassion CH (<https://www.compassion.ch>)
# @author: Simon Gonzalez <simon.gonzalez@bluewin.ch>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "l10n_ch_import_payment_return",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Compassion CH,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-switzerland",
    "category": "Banking addons",
    "depends": ["account_payment_export_sftp"],  # OCA/bank-payment
    "data": ["data/edi_data.xml"],
    "installable": True,
}
