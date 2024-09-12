from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    print_qr_invoice = fields.Boolean(
        string="Print invoice with QR bill",
        default=True,
    )
    invoice_report_id = fields.Many2one("ir.actions.report", string="Invoice Report")
    qr_report_id = fields.Many2one("ir.actions.report", string="QR Report")
