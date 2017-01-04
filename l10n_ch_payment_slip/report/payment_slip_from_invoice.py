# -*- coding: utf-8 -*-
# © 2014-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class BVRFromInvoice(models.AbstractModel):
    _name = 'report.one_slip_per_page_from_invoice'


class ExtendedReport(models.Model):

    _inherit = 'report'

    @api.multi
    def _generate_one_slip_per_page_from_invoice_pdf(self, report_name=None):
        """Generate payment slip PDF(s) from report model.
        If there is many pdf they are merged in memory or on
        file system based on company settings

        :return: the generated PDF content
        """
        user_model = self.env['res.users']
        slip_model = self.env['l10n_ch.payment_slip']
        invoice_model = self.env['account.invoice']
        company = user_model.browse().company_id
        invoices = invoice_model.browse()

        docs = slip_model._compute_pay_slips_from_invoices(invoices)
        if len(docs) == 1:
            return docs[0]._draw_payment_slip(a4=True,
                                              b64=False,
                                              report_name=report_name,
                                              out_format='PDF')
        else:
            pdfs = (x._draw_payment_slip(a4=True, b64=False, out_format='PDF',
                                         report_name=report_name)
                    for x in docs)
            if company.merge_mode == 'in_memory':
                return self.merge_pdf_in_memory(pdfs)
            return self.merge_pdf_on_disk(pdfs)

    @api.multi
    def get_pdf(self, report_name, html=None, data=None):
        if (report_name == 'l10n_ch_payment_slip.'
                           'one_slip_per_page_from_invoice'):
            return self._generate_one_slip_per_page_from_invoice_pdf(
                report_name=report_name,
            )
        else:
            return super(ExtendedReport, self).get_pdf(
                report_name,
                html=html,
                data=data
            )
