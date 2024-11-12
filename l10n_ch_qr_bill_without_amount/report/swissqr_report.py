from odoo import api, models


class ReportSwissQR(models.AbstractModel):
    _inherit = "report.l10n_ch.qr_report_main"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["account.move"].browse(docids)
        qr_bill_without_amount = {}
        for invoice in docs:
            if invoice.payment_mode_id.qr_bill_without_amount:
                # We sent invoice ref or name in context to be able to retrieve
                # it in res.partner.bank._l10n_ch_get_qr_vals
                qr_bill_without_amount[
                    invoice.ref or invoice.name
                ] = invoice.payment_mode_id.qr_bill_without_amount
        self = self.with_context(qr_bill_without_amount=qr_bill_without_amount)
        return super(ReportSwissQR, self)._get_report_values(docids, data)
