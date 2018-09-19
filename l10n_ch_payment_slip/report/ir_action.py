# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
import tempfile
import io
import logging
from contextlib import closing
import base64
import time

from odoo import models, fields, api
from odoo.exceptions import AccessError
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


try:
    import PyPDF2
except (ImportError, IOError) as err:
    _logger.debug(err)


class IrActionsReportReportlab(models.Model):

    _inherit = 'ir.actions.report'

    report_type = fields.Selection(selection_add=[('reportlab-pdf',
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
                    'loaded_documents' in save_in_attachment and
                    save_in_attachment['loaded_documents'].get(
                        doc.invoice_id.id)
            ):
                with closing(os.fdopen(pdfreport_fd, 'w')) as pdfreport:
                    pdfreport.write(save_in_attachment['loaded_documents']
                                    [doc.invoice_id.id])
                pdfdocuments.append(pdfreport_path)
                continue

            with closing(os.fdopen(pdfreport_fd, 'wb')) as pdfreport:
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
                        'datas': base64.encodestring(pdfreport.read()),
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
                entire_report_path = self.merge_pdf_on_disk(pdfdocuments)

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
            report = self.search([
                ('report_type', '=', 'reportlab-pdf'),
                ('report_name', '=', report_name)],
                limit=1
            )
        return report

    @api.multi
    def render_reportlab_pdf(self, res_ids=None, data=None):
        if (self.report_name != 'l10n_ch_payment_slip.'
                'one_slip_per_page_from_invoice') or not res_ids:
            return

        save_in_attachment = {}

        # Dispatch the records by ones having an attachment and ones
        # requesting a call to reportlab. (copied from render_qweb_pdf)
        Model = self.env[self.model]
        records = Model.browse(res_ids)
        if self.attachment:
            for rec in records:
                attachment_id = self.retrieve_attachment(rec)
                if attachment_id:
                    save_in_attachment['loaded_documents'][
                        rec.id] = attachment_id
                else:
                    attachment_name = safe_eval(
                        self.attachment, {'object': rec, 'time': time})
                    save_in_attachment[rec.id] = attachment_name
        if save_in_attachment:
            save_in_attachment['model'] = self.model

        reports = self.browse(res_ids)
        # Unlike render_qweb_pdf we don't call _post_pdf in order to
        # add the option of using temporaty files, this is done in the
        # following call thus we already take care of creating attachments.
        pdf_content = reports._generate_one_slip_per_page_from_invoice_pdf(
            report_name=self.report_name,
            save_in_attachment=save_in_attachment,
        )
        return pdf_content, 'pdf'

    def merge_pdf_in_memory(self, docs):
        merger = PyPDF2.PdfFileMerger()
        for doc in docs:
            merger.append(doc)
        buff = io.BytesIO()
        try:
            # The writer close the reader file here
            merger.write(buff)
            return buff.getvalue()
        except IOError:
            raise
        finally:
            buff.close()

    def merge_pdf_on_disk(self, docs):
        merger = PyPDF2.PdfFileMerger()
        for doc in docs:
            merger.append(doc)
        buff, buff_path = tempfile.mkstemp(
            suffix='.pdf',
            prefix='credit_control_slip_merged')
        try:
            buff = os.fdopen(buff, 'w+b')
            # The writer close the reader file here
            buff.seek(0)
            merger.write(buff)
            buff.seek(0)
            return buff_path
        except IOError:
            raise
        finally:
            buff.close()
