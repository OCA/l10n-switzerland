# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os

from odoo import models
from odoo.modules.module import get_module_root

MODULE_PATH = get_module_root(os.path.dirname(__file__))
INVOICE_LINE_STOCK_TEMPLATE = "invoice-line-stock-yellowbill.jinja"
TEMPLATE_DIR = [MODULE_PATH + "/messages"]


class EbillPostfinanceInvoiceMessage(models.Model):
    _inherit = "ebill.postfinance.invoice.message"

    def _get_jinja_env(self, template_dir):
        template_dir += TEMPLATE_DIR
        return super()._get_jinja_env(template_dir)

    def _get_payload_params_yb(self):
        params = super()._get_payload_params_yb()
        params["invoice_line_stock_template"] = INVOICE_LINE_STOCK_TEMPLATE
        return params
