from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    print_qr_invoice = fields.Boolean(
        related="company_id.print_qr_invoice",
        string="Print invoice with QR bill",
        readonly=False,
    )
