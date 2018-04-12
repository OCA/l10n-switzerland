# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
import tempfile
import io
import logging
from contextlib import closing
import base64

from odoo import models, fields, api
from odoo.exceptions import AccessError


_logger = logging.getLogger(__name__)


try:
    import PyPDF2
except (ImportError, IOError) as err:
    _logger.debug(err)


class IrActionsReportReportlab(models.Model):

    _inherit = 'ir.actions.report'

    report_type = fields.Selection(selection_add=[('reportlab_pdf',
                                                   'Report renderer')])

    @api.multi
    def _generate_one_slip_per_page_from_invoice_pdf(self, report_name=None,
                                                     save_in_attachment=None):
        """Generate payment slip PDF(s) from report model.

        If there are many pdf they are merged in memory or on
        file system based on company settings

        :return: the generated PDF content
        """
        if not save_in_attachment:
            save_in_attachment = {}
        user_model = self.env['res.users']
        slip_model = self.env['l10n_ch.payment_slip']
        invoice_model = self.env['account.invoice']
        company = user_model.browse(self.env.uid).company_id
        invoices = invoice_model.browse(self.ids)

        docs = slip_model._compute_pay_slips_from_invoices(invoices)

        pdfdocuments = []
        temporary_files = []

        for doc in docs:
            pdfreport_fd, pdfreport_path = tempfile.mkstemp(
                suffix='.pdf', prefix='report.tmp.')
            temporary_files.append(pdfreport_path)

            # Directly load the document if we already have it
            if (
                    save_in_attachment and
                    save_in_attachment['loaded_documents'].get(
                        doc.invoice_id.id)
            ):
                with closing(os.fdopen(pdfreport_fd, 'w')) as pdfreport:
                    pdfreport.write(save_in_attachment['loaded_documents']
                                    [doc.invoice_id.id])
                pdfdocuments.append(pdfreport_path)
                continue

            with closing(os.fdopen(pdfreport_fd, 'w')) as pdfreport:
                pdf = doc._draw_payment_slip(a4=True, b64=False,
                                             out_format='PDF',
                                             report_name=report_name)
                pdfreport.write(pdf)

            # Save the pdf in attachment if marked
            if save_in_attachment and save_in_attachment.get(
                    doc.invoice_id.id):
                with open(pdfreport_path, 'rb') as pdfreport:
                    attachment = {
                        'name': save_in_attachment.get(doc.invoice_id.id),
                        'datas': base64.encodebytes(pdfreport.read()),
                        'datas_fname': save_in_attachment.get(
                            doc.invoice_id.id),
                        'res_model': save_in_attachment.get('model'),
                        'res_id': doc.invoice_id.id,
                    }
                    try:
                        self.env['ir.attachment'].create(attachment)
                    except AccessError:
                        _logger.info("Cannot save PDF report %r as attachment",
                                     attachment['name'])
                    else:
                        _logger.info(
                            'The PDF document %s is now saved in the database',
                            attachment['name'])

            pdfdocuments.append(pdfreport_path)

        # Return the entire document
        if len(pdfdocuments) == 1:
            entire_report_path = pdfdocuments[0]
        else:
            if company.merge_mode == 'in_memory':
                content = self.merge_pdf_in_memory(pdfdocuments)
                entire_report_path = False
            else:
                entire_report_path = self._merge_pdf(pdfdocuments)

        if entire_report_path:
            with open(entire_report_path, 'rb') as pdfdocument:
                content = pdfdocument.read()
            if entire_report_path not in temporary_files:
                temporary_files.append(entire_report_path)

        # Manual cleanup of the temporary files
        for temporary_file in temporary_files:
            try:
                os.unlink(temporary_file)
            except (OSError, IOError):
                _logger.error(
                    'Error when trying to remove file %s' % temporary_file)

        return content

    @api.model
    def _get_report_from_name(self, report_name):
        """Return also report of report_type reportlab-pdf and not only qweb
        """
        report = super()._get_report_from_name(report_name)
        if not report:
            report = report.search([
                ('report_type', '=', 'reportlab-pdf'),
                ('report_name', '=', report_name)],
                limit=1
            )
        return report

    @api.multi
    def get_pdf(self, docids, report_name, html=None, data=None):
        if (report_name == 'l10n_ch_payment_slip.'
                           'one_slip_per_page_from_invoice'):
            report = self._get_report_from_name(report_name)
            save_in_attachment = self._check_attachment_use(
                docids, report)

            reports = self.browse(docids)
            return reports._generate_one_slip_per_page_from_invoice_pdf(
                report_name=report_name, save_in_attachment=save_in_attachment
            )
        else:
            return super().get_pdf(docids, report_name, html=html, data=data)

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
        writer = PyPDF2.PdfFileWriter()
        for doc in docs:
            pdfreport = os.fdopen(doc, 'rb')
            reader = PyPDF2.PdfFileReader(pdfreport)
            for page in range(reader.getNumPages()):
                writer.addPage(reader.getPage(page))
        buff = io.BytesIO()
        try:
            # The writer close the reader file here
            writer.write(buff)
            return buff.getvalue()
        except IOError:
            raise
        finally:
            buff.close()

    def merge_pdf_on_disk(self, docs):
        writer = PyPDF2.PdfFileWriter()
        for doc in docs:
            pdfreport = os.fdopen(doc, 'rb')
            reader = PyPDF2.PdfFileReader(pdfreport)
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
