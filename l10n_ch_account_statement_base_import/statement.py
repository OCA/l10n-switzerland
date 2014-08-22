# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino
#    Copyright 2014 Compassion CH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tools.translate import _
from openerp.osv.orm import Model
from openerp.osv import osv

import tempfile
import tarfile
import base64
import datetime


class AccountStatementProfil(Model):
    _inherit = "account.statement.profile"

    def _get_import_type_selection(self, cr, uid, context=None):
        res = super(AccountStatementProfil, self)._get_import_type_selection(
            cr, uid, context=context)
        res.extend([('raiffeisen_csvparser',
                     'Parser for Raiffeisen (CH-FR) statements'),
                    ('raiffeisen_details_csvparser',
                     'Parser for detailed Raiffeisen (CH-FR) statements'),
                    ('ubs_csvparser', 'Parser for UBS (CH-FR) statements'),
                    ('pf_xmlparser', 'Parser for Postfinance XML statements'),
                    ('esr_fileparser', 'Parser for ESR Payment Slips'),
                    ('g11_fileparser',
                     'Parser for Postfinance BVR DD type 2')])
        return res

    def prepare_statement_vals(self, cr, uid, profile_id, result_row_list,
                               parser, context):
        """
        Before creating bank statement, we check for .g11 files that the
        currency of the transactions are the same that the one of the company.
        """
        if hasattr(parser, 'currency'):
            journal = self.browse(cr, uid, profile_id,
                                  context=context).journal_id
            if not (parser.currency == journal.currency.name or
                    parser.currency == journal.company_id.currency_id.name):
                raise osv.except_osv(_("Wrong currency"),
                                     _("The transactions you are importing \
                                     are not in the same currency than the \
                                     selected journal !"))

        return super(AccountStatementProfil, self).prepare_statement_vals(
            cr, uid, profile_id, result_row_list, parser, context)

    def _statement_import(self, cr, uid, ids, prof, parser, file_stream,
                          ftype="csv", context=None):
        """
        Save the file_stream because it is modified in the XML parser.
        """
        self.file_stream = file_stream

        return super(AccountStatementProfil, self)._statement_import(
            cr, uid, ids, prof, parser, file_stream, ftype, context)

    def _write_extra_statement_lines(self, cr, uid, parser, result_row_list,
                                     profile, statement_id, context):
        """ For Postfinance XML parser, we join the attached documents to
            the statement. """
        if parser.parser_for('pf_xmlparser'):
            pf_file = tempfile.NamedTemporaryFile()
            pf_file.write(base64.b64decode(self.file_stream))
            # We ensure that cursor is at beginning of file
            pf_file.seek(0)

            tfile = tarfile.open(fileobj=pf_file, mode="r:gz")
            for filename in tfile.getnames():
                if filename[-3:] not in ['xml', 'png']:
                    continue
                data = None
                if filename[-3:] == 'png':
                    data = tfile.extractfile(filename).read()
                else:
                    data = tfile.extractfile(filename).read().encode('base64')
                attachment_data = {
                    'name': filename,
                    'datas': data,
                    'datas_fname': "%s.%s" % (
                        datetime.datetime.now().date(), filename[-4:]),
                    'res_model': 'account.bank.statement',
                    'res_id': statement_id,
                }
                self.pool.get('ir.attachment').create(
                    cr, uid, attachment_data, context=context)
