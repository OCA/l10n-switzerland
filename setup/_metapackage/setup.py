import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-l10n-switzerland",
    description="Meta package for oca-l10n-switzerland Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-l10n_ch_bank',
        'odoo10-addon-l10n_ch_bank_statement_import_postfinance',
        'odoo10-addon-l10n_ch_base_bank',
        'odoo10-addon-l10n_ch_dta',
        'odoo10-addon-l10n_ch_fds_postfinance',
        'odoo10-addon-l10n_ch_fds_upload_dd',
        'odoo10-addon-l10n_ch_fds_upload_sepa',
        'odoo10-addon-l10n_ch_hr_payroll',
        'odoo10-addon-l10n_ch_hr_payroll_report',
        'odoo10-addon-l10n_ch_import_cresus',
        'odoo10-addon-l10n_ch_import_pain002',
        'odoo10-addon-l10n_ch_import_winbiz',
        'odoo10-addon-l10n_ch_lsv_dd',
        'odoo10-addon-l10n_ch_pain_base',
        'odoo10-addon-l10n_ch_pain_credit_transfer',
        'odoo10-addon-l10n_ch_payment_slip',
        'odoo10-addon-l10n_ch_scan_bvr',
        'odoo10-addon-l10n_ch_states',
        'odoo10-addon-l10n_ch_zip',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
