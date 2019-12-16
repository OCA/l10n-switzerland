import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-l10n-switzerland",
    description="Meta package for oca-l10n-switzerland Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-l10n_ch_account_tags',
        'odoo11-addon-l10n_ch_bank',
        'odoo11-addon-l10n_ch_bank_statement_import_postfinance',
        'odoo11-addon-l10n_ch_base_bank',
        'odoo11-addon-l10n_ch_fds_postfinance',
        'odoo11-addon-l10n_ch_hr_payroll',
        'odoo11-addon-l10n_ch_import_isr_v11',
        'odoo11-addon-l10n_ch_invoice_with_payment',
        'odoo11-addon-l10n_ch_mis_reports',
        'odoo11-addon-l10n_ch_pain_base',
        'odoo11-addon-l10n_ch_pain_credit_transfer',
        'odoo11-addon-l10n_ch_payment_slip',
        'odoo11-addon-l10n_ch_scan_bvr',
        'odoo11-addon-l10n_ch_states',
        'odoo11-addon-l10n_ch_zip',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
