import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-l10n-switzerland",
    description="Meta package for oca-l10n-switzerland Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-l10n_ch_account_statement_base_import',
        'odoo8-addon-l10n_ch_bank',
        'odoo8-addon-l10n_ch_base_bank',
        'odoo8-addon-l10n_ch_credit_control_payment_slip_report',
        'odoo8-addon-l10n_ch_dta',
        'odoo8-addon-l10n_ch_dta_base_transaction_id',
        'odoo8-addon-l10n_ch_fds_postfinance',
        'odoo8-addon-l10n_ch_fds_upload_dd',
        'odoo8-addon-l10n_ch_fds_upload_sepa',
        'odoo8-addon-l10n_ch_hr_payroll',
        'odoo8-addon-l10n_ch_import_cresus',
        'odoo8-addon-l10n_ch_lsv_dd',
        'odoo8-addon-l10n_ch_payment_slip',
        'odoo8-addon-l10n_ch_payment_slip_base_transaction_id',
        'odoo8-addon-l10n_ch_payment_slip_layouts',
        'odoo8-addon-l10n_ch_payment_slip_voucher',
        'odoo8-addon-l10n_ch_scan_bvr',
        'odoo8-addon-l10n_ch_sepa',
        'odoo8-addon-l10n_ch_states',
        'odoo8-addon-l10n_ch_zip',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
