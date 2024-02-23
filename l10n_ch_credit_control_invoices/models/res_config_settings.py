from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    credit_ctrl_print_invoice = fields.Boolean(
        related="company_id.credit_ctrl_print_invoice",
        string="Print credit control summary with invoices",
        readonly=False,
    )
