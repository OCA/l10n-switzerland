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
        reports_list = []
        inv_report = self._get_report_from_name('account.report_invoice')
        invoice_pdf, _ = inv_report.with_context(
            ctx).render_qweb_pdf(res_ids, data)
        reports_list.append(invoice_pdf)
        inv_record = self.env[self.model].browse(res_ids)
        if inv_record.company_id.print_isr_invoice:
            slip_report = self._get_report_from_name(
                'l10n_ch_payment_slip.one_slip_per_page_from_invoice'
            )
            payment_slip_pdf, _ = slip_report.render_reportlab_pdf(res_ids, data)
            reports_list.append(payment_slip_pdf)
            
        if inv_record.company_id.print_qr_invoice:
            qr_report = self._get_report_from_name('l10n_ch.qr_report_main')
            qr_report_pdf, _ =  qr_report.render_reportlab_pdf(res_ids,data)
            reports_list.append(qr_report_pdf)
        io_list = [io.BytesIO(pdf_file) for pdf_file in reports_list]
        return (self.merge_pdf_in_memory(io_list),
                'pdf')
