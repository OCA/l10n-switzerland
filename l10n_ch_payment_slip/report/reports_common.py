# -*- coding: utf-8 -*-
# © 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
import tempfile
import StringIO
import pyPdf
from openerp import models


class CommonSlipReport(models.Model):

    _inherit = 'report'

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
