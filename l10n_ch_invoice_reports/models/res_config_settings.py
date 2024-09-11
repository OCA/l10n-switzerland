from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    print_qr_invoice = fields.Boolean(
        related="company_id.print_qr_invoice",
        string="Print invoice with QR bill",
        readonly=False,
    )
    invoice_report_id = fields.Many2one(
        related="company_id.invoice_report_id",
        string="Invoice Report",
        readonly=False,
        config_parameter="invoice_report_id",
    )
    qr_report_id = fields.Many2one(
        related="company_id.qr_report_id",
        string="QR Report",
        readonly=False,
        config_parameter="qr_report_id",
    )
