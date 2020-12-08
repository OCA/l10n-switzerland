# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

from odoo import models
from odoo.modules.module import get_module_root

MODULE_PATH = get_module_root(os.path.dirname(__file__))
DISCOUNT_TEMPLATE = "discount-2003A.xml.jinja"
TEMPLATE_DIR = [MODULE_PATH + "/messages"]


class PaynetInvoiceMessage(models.Model):
    _inherit = "paynet.invoice.message"

    def _get_jinja_env(self, template_dir):
        template_dir += TEMPLATE_DIR
        return super()._get_jinja_env(template_dir)

    def _get_payload_params(self):
        params = super()._get_payload_params()
        params["discount_template"] = DISCOUNT_TEMPLATE
        discount = {}
        if self.invoice_id.invoice_payment_term_id.percent_discount:
            terms = self.invoice_id.invoice_payment_term_id
            discount = {
                "percentage": terms.percent_discount,
                "days": terms.days_discount,
            }
        params["discount"] = discount
        return params
