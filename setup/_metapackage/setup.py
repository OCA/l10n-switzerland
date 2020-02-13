import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-l10n-switzerland",
    description="Meta package for oca-l10n-switzerland Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-l10n_ch_account_tags',
        'odoo12-addon-l10n_ch_bank',
        'odoo12-addon-l10n_ch_base_bank',
        'odoo12-addon-l10n_ch_invoice_with_payment',
        'odoo12-addon-l10n_ch_mis_reports',
        'odoo12-addon-l10n_ch_pain_base',
        'odoo12-addon-l10n_ch_pain_credit_transfer',
        'odoo12-addon-l10n_ch_payment_slip',
        'odoo12-addon-l10n_ch_states',
        'odoo12-addon-l10n_ch_zip',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
