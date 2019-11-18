# © 2017-2018 Compassion CH (Marco Monzione)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Import pain002',
    'version': '11.0.0.0.0',
    'license': 'AGPL-3',
    'author': 'Monzione Marco, Odoo Community Association (OCA)',
    'website': 'https://www.compassion.ch',
    'category': 'Banking addons',
    'depends': [
        'account_payment_order',
        'account_bank_statement_import_camt_oca',  # oca_addons/bank-payment
        'account_payment_line_cancel',
    ],
    'data': [
        'wizards/import_payment_return_wizard_view.xml',
    ],
    # 'demo': [
    #     'test_files/test_data.yml',
    # ],
    'installable': True,
}
