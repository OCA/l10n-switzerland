import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-switzerland",
    description="Meta package for oca-l10n-switzerland Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-ebill_paynet',
        'odoo14-addon-l10n_ch_account_tags',
        'odoo14-addon-l10n_ch_base_bank',
        'odoo14-addon-l10n_ch_invoice_reports',
        'odoo14-addon-l10n_ch_isrb',
        'odoo14-addon-l10n_ch_states',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
