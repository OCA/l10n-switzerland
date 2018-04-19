import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-l10n-switzerland",
    description="Meta package for oca-l10n-switzerland Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-l10n_ch_bank',
        'odoo9-addon-l10n_ch_bank_statement_import_postfinance',
        'odoo9-addon-l10n_ch_base_bank',
        'odoo9-addon-l10n_ch_dta',
        'odoo9-addon-l10n_ch_fds_postfinance',
        'odoo9-addon-l10n_ch_fds_upload_dd',
        'odoo9-addon-l10n_ch_fds_upload_sepa',
        'odoo9-addon-l10n_ch_hr_payroll',
        'odoo9-addon-l10n_ch_import_cresus',
        'odoo9-addon-l10n_ch_import_winbiz',
        'odoo9-addon-l10n_ch_lsv_dd',
        'odoo9-addon-l10n_ch_pain_base',
        'odoo9-addon-l10n_ch_pain_credit_transfer',
        'odoo9-addon-l10n_ch_payment_slip',
        'odoo9-addon-l10n_ch_scan_bvr',
        'odoo9-addon-l10n_ch_states',
        'odoo9-addon-l10n_ch_zip',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
