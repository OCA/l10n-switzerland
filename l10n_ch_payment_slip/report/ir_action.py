# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
import tempfile
import io
import PyPDF2

from odoo import models, fields, api


class IrActionsReportReportlab(models.Model):

    _inherit = 'ir.actions.report'

    report_type = fields.Selection(selection_add=[('reportlab_pdf',
                                                   'Report renderer')])

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
        company = user_model.browse(self.env.uid).company_id
        invoices = invoice_model.browse(self.ids)

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
    def render_reportlab_pdf(self, docids, data=None):
        if (self.report_name == 'l10n_ch_payment_slip.'
                'one_slip_per_page_from_invoice'):
            reports = self.browse(docids)
            pdf_content = reports._generate_one_slip_per_page_from_invoice_pdf(
                report_name=self.report_name,
            )
            return pdf_content, 'pdf'

    def merge_pdf_in_memory(self, docs):
        streams = []
        merger = PyPDF2.PdfFileMerger()
        for doc in docs:
            current_buff = io.BytesIO()
            streams.append(current_buff)
            current_buff.write(doc)
            current_buff.seek(0)
            merger.append(PyPDF2.PdfFileReader(current_buff))
        buff = io.BytesIO()
        try:
            # The writer close the reader file here
            merger.write(buff)
            return buff.getvalue()
        except IOError:
            raise
        finally:
            buff.close()
            for stream in streams:
                stream.close()

    def merge_pdf_on_disk(self, docs):
        streams = []
        writer = PyPDF2.PdfFileWriter()
        for doc in docs:
            current_buff = tempfile.mkstemp(
                suffix='.pdf',
                prefix='credit_control_slip')[0]
            current_buff = os.fdopen(current_buff, 'w+b')
            current_buff.seek(0)
            streams.append(current_buff)
            current_buff.write(doc)
            current_buff.seek(0)
            reader = PyPDF2.PdfFileReader(current_buff)
            for page in range(reader.getNumPages()):
                writer.addPage(reader.getPage(page))
        buff = tempfile.mkstemp(
            suffix='.pdf',
            prefix='credit_control_slip_merged')[0]
        try:
            buff = os.fdopen(buff, 'w+b')
            # The writer close the reader file here
            buff.seek(0)
            writer.write(buff)
            buff.seek(0)
            return buff.read()
        except IOError:
            raise
        finally:
            buff.close()
            for stream in streams:
                stream.close()
