from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    credit_ctrl_print_invoice = fields.Boolean(
        string="Print credit control summary with invoices",
        default=True,
    )
