import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-l10n-switzerland",
    description="Meta package for oca-l10n-switzerland Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-l10n_ch_account_tags',
        'odoo13-addon-l10n_ch_base_bank',
        'odoo13-addon-l10n_ch_invoice_reports',
        'odoo13-addon-l10n_ch_isr_payment_grouping',
        'odoo13-addon-l10n_ch_isrb',
        'odoo13-addon-l10n_ch_states',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
