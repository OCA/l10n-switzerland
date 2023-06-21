import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-switzerland",
    description="Meta package for oca-l10n-switzerland Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-ebill_paynet',
        'odoo14-addon-ebill_paynet_customer_free_ref',
        'odoo14-addon-l10n_ch_account_tags',
        'odoo14-addon-l10n_ch_base_bank',
        'odoo14-addon-l10n_ch_delivery_carrier_label_quickpac',
        'odoo14-addon-l10n_ch_invoice_reports',
        'odoo14-addon-l10n_ch_isr_payment_grouping',
        'odoo14-addon-l10n_ch_isrb',
        'odoo14-addon-l10n_ch_mis_reports',
        'odoo14-addon-l10n_ch_states',
        'odoo14-addon-server_env_ebill_paynet',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
