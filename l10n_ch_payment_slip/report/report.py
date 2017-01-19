# -*- coding: utf-8 -*-
# © 2014-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api
import os
import tempfile
import StringIO
import pyPdf


class BVRFromInvoice(models.AbstractModel):
    _name = 'report.one_slip_per_page_from_invoice'


class Report(models.Model):

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
    def get_pdf(self, docids, report_name, html=None, data=None):
        if (report_name == 'l10n_ch_payment_slip.'
                           'one_slip_per_page_from_invoice'):
            reports = self.browse(docids)
            return reports._generate_one_slip_per_page_from_invoice_pdf(
                report_name=report_name,
            )
        else:
            return super(Report, self).get_pdf(docids, report_name, html=html,
                                               data=data)

    def merge_pdf_in_memory(self, docs):
        streams = []
        writer = pyPdf.PdfFileWriter()
        for doc in docs:
            current_buff = StringIO.StringIO()
            streams.append(current_buff)
            current_buff.write(doc)
            current_buff.seek(0)
            reader = pyPdf.PdfFileReader(current_buff)
            for page in xrange(reader.getNumPages()):
                writer.addPage(reader.getPage(page))
        buff = StringIO.StringIO()
        try:
            # The writer close the reader file here
            writer.write(buff)
            return buff.getvalue()
        except IOError:
            raise
        finally:
            buff.close()
            for stream in streams:
                stream.close()

    def merge_pdf_on_disk(self, docs):
        streams = []
        writer = pyPdf.PdfFileWriter()
        for doc in docs:
            current_buff = tempfile.mkstemp(
                suffix='.pdf',
                prefix='credit_control_slip')[0]
            current_buff = os.fdopen(current_buff, 'w+b')
            current_buff.seek(0)
            streams.append(current_buff)
            current_buff.write(doc)
            current_buff.seek(0)
            reader = pyPdf.PdfFileReader(current_buff)
            for page in xrange(reader.getNumPages()):
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
