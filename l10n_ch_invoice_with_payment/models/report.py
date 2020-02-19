# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import io
from odoo import models, api


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        ctx = self.env.context
        # Remove context key that comes from invoice action
        if ctx.get('default_type'):
            ctx = ctx.copy()
            ctx.pop('default_type')
        if (self.report_name != 'l10n_ch_invoice_with_payment.'
                'report_invoice_with_paymentslip' or not res_ids):
            return super().render_qweb_pdf(res_ids, data)
        inv_report = self._get_report_from_name('account.report_invoice')
        invoice_pdf, _ = inv_report.with_context(
            ctx).render_qweb_pdf(res_ids, data)
        invoice_pdf_io = io.BytesIO(invoice_pdf)

        slip_report = self._get_report_from_name(
            'l10n_ch_payment_slip.one_slip_per_page_from_invoice'
        )
        payment_slip_pdf, _ = slip_report.render_reportlab_pdf(res_ids, data)
        payment_pdf_io = io.BytesIO(payment_slip_pdf)

        return (self.merge_pdf_in_memory([invoice_pdf_io, payment_pdf_io]),
                'pdf')
