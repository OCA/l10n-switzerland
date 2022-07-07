# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Quickpac",
    "version": "14.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainer": "Camptocamp",
    "summary": "Print quickpac shipping labels",
    "category": "Delivery",
    "complexity": "normal",
    "depends": [
        "base_delivery_carrier_label",
        "delivery_carrier_label_batch",
        "configuration_helper",
        "stock",
    ],
    "website": "https://github.com/OCA/l10n-switzerland",
    "data": [
        "data/product.xml",
        "data/partner.xml",
        "data/delivery_template_option.xml",
        "data/delivery.xml",
        "data/delivery_option.xml",
        "views/delivery.xml",
        "views/res_config.xml",
    ],
    "external_dependencies": {
        "python": [
            "quickpac",
            "unidecode",
        ],
    },
    "installable": True,
    "license": "AGPL-3",
    "auto_install": False,
    "application": True,
}
