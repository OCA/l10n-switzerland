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
from openerp.osv import orm, fields

import tempfile
import tarfile
import base64
from datetime import date
import hashlib


class AccountBankStatement(orm.Model):
    _inherit = "account.bank.statement"

    _columns = {
        'checksum': fields.char(_('Checksum')),
        }


class AccountStatementProfil(orm.Model):
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
                raise orm.except_orm(_("Wrong currency"),
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

        """
        Calculate hash of the file to determinate if it already exist
        """
        hash = hashlib.md5(file_stream).hexdigest()
        statement_obj = self.pool.get('account.bank.statement')

        for statement_id in statement_obj.search(
                cr, uid, [('profile_id', '=', prof.id)], context=context):
            statement = statement_obj.browse(cr, uid, statement_id,
                                             context=context)
            if statement.checksum and (statement.checksum == hash):
                raise orm.except_orm(_("Warning"),
                                     _("Bank statement already imported on %s")
                                     % statement.date)

        id_new_statement = super(AccountStatementProfil, self). \
            _statement_import(cr, uid, ids, prof, parser, file_stream, ftype,
                              context)

        statement_obj.write(cr, uid, [id_new_statement], {'checksum': hash},
                            context=context)

        return id_new_statement

    def _write_extra_statement_lines(self, cr, uid, parser, result_row_list,
                                     profile, statement_id, context):
        """ For Postfinance XML parser, we join the attached documents to
            the statement_line or to the statement if a corresponding line
            is not found. """
        if parser.parser_for('pf_xmlparser'):
            pf_file = tempfile.NamedTemporaryFile()
            pf_file.write(base64.b64decode(self.file_stream))
            # We ensure that cursor is at beginning of file
            pf_file.seek(0)

            tfile = tarfile.open(fileobj=pf_file, mode="r:gz")
            for filename in tfile.getnames():
                if filename[-3:] not in ['xml', 'png']:
                    continue
                data = tfile.extractfile(filename).read().encode('base64')
                # Attach to bank statement by default
                res_model = 'account.bank.statement'
                res_id = statement_id
                # Search statement_line concerned
                statement = self.pool.get(res_model).browse(
                    cr, uid, statement_id, context)
                for st_line in statement.line_ids:
                    if st_line.ref == filename[:-4]:
                        res_model = 'account.bank.statement.line'
                        res_id = st_line.id
                        break

                attachment_data = {
                    'name': filename,
                    'datas': data,
                    'datas_fname': "%s.%s" % (
                        date.today(), filename[-4:]),
                    'res_model': res_model,
                    'res_id': res_id,
                }
                self.pool.get('ir.attachment').create(
                    cr, uid, attachment_data, context=context)


class AccountStatementLine(orm.Model):
    """ Adds a field to retrieve attachment file of a line. """

    _inherit = 'account.bank.statement.line'

    def _get_attachment(self, cr, uid, ids, name, args, context=None):
        attachment_obj = self.pool.get('ir.attachment')
        res = dict()
        for st_line in self.browse(cr, uid, ids, context):
            attachment_ids = attachment_obj.search(
                cr, uid, [('res_model', '=', self._name),
                          ('res_id', '=', st_line.id)],
                limit=1, context=context)
            if not attachment_ids:
                res[st_line.id] = False
                continue

            if name == 'file_name':
                res[st_line.id] = _('View file')
            elif name == 'ir_attachment':
                res[st_line.id] = attachment_ids[0]
        return res

    _columns = {
        'file_name': fields.function(_get_attachment, type='char',
                                     string=_('Attachment')),
        'ir_attachment': fields.function(
            _get_attachment, type='many2one', obj='ir.attachment',
            string='Attachment'),
    }

    def download_attachment(self, cr, uid, ids, context=None):
        st_line = self.browse(cr, uid, ids[0], context)
        view_id = self.pool.get('ir.model.data').get_object_reference(
            cr, uid, 'l10n_ch_account_statement_base_import',
            'attachement_form_postfinance')[1]
        if st_line.ir_attachment:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Attachment',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'ir.attachment',
                'view_id': view_id,
                'res_id': st_line.ir_attachment.id,
                'target': 'new',
            }
        return True
