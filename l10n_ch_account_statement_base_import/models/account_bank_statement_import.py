# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2015 Camptocamp SA
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
from openerp import models, api, _, exceptions, fields
from ..parsers import base_parser


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    related_files = fields.Many2many(
        comodel_name='ir.attachment',
        string='Related files',
        readonly=True
    )
    file_name = fields.Char(compute='_get_attachment')

    @api.model
    def get_statement_line_for_reconciliation(self, st_line):
        data = super(AccountBankStatementLine,
                     self).get_statement_line_for_reconciliation(st_line)
        for related_file in st_line.related_files:
            image = "data:" + related_file.file_type + ";base64," + \
                related_file.datas
            data['img_src'] = ['src', image]
            data['modal_id'] = ['id', 'img' + str(related_file.id)]
            data['data_target'] = [
                'data-target', '#img' + str(related_file.id)]
        return data

    @api.one
    def _get_attachment(self):
        if self.related_files:
            self.file_name = _('View file')
        else:
            self.file_name = ''

    @api.multi
    def download_attachment(self):
        self.ensure_one()
        view_id = self.env['ir.model.data'].get_object_reference(
            'l10n_ch_account_statement_base_import',
            'attachement_form_postfinance')[1]
        for related_file in self.related_files:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Attachment',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'ir.attachment',
                'view_id': view_id,
                'res_id': related_file.id,
                'target': 'new',
            }
        return True


class AccountBankStatementImport(models.TransientModel):

    _inherit = 'account.bank.statement.import'

    @api.model
    def _get_hide_journal_field(self):
        return self.env.context.get('journal_id') and True

    @api.model
    def _parse_file(self, data_file):
        """ Each module adding a file support must extends this method.
        It processes the file if it can, returns super otherwise,
        resulting in a chain of responsability.
        This method parses the given file and returns the data required
        by the bank statement import process, as specified below.
            rtype: triplet (if a value can't be retrieved, use None)
                - currency code: string (e.g: 'EUR')
                    The ISO 4217 currency code, case insensitive
                - account number: string (e.g: 'BE1234567890')
                 The number of the bank account which the statement belongs to
                - bank statements data: list of dict containing
                    (optional items marked by o) :
                    - 'name': string (e.g: '000000123')
                    - 'date': date (e.g: 2013-06-26)
                    -o 'balance_start': float (e.g: 8368.56)
                    -o 'balance_end_real': float (e.g: 8888.88)
                    - 'transactions': list of dict containing :
                        - 'name': string
                          (e.g: 'KBC-INVESTERINGSKREDIET 787-5562831-01')
                        - 'date': date
                        - 'amount': float
                        - 'unique_import_id': string
                        -o 'account_number': string
                            Will be used to find/create the
                             res.partner.bank in odoo
                        -o 'note': string
                        -o 'partner_name': string
                        -o 'ref': string

        the abstract function is defined by account_bank_statement_import

        :param data_file: the raw content of the file to be imported
        :type data_file: string
        """
        for parser in self._get_parsers(data_file):
            if parser.file_is_known():
                parser.parse()
                currency_code = parser.get_currency()
                account_number = parser.get_account_number()
                statements = parser.get_statements()

                if not statements:
                    raise exceptions.Warning(_('Nothing to import'))
                return currency_code, account_number, statements
        else:
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

    @api.model
    def _get_parsers(self, data_file):
        """Return a generator of available file parser instances.
        The instances are initialized with the file content.
        In order to be recognized as a parser a class must
        extend :py:class:`Base_parser` and be imported at least once

        :param data_file: the raw content of the file to be imported
        :type data_file: string

        :return: A generator of available parser instances
        :rtype: generator of available parser instances

        """
        for parser_class in base_parser.BaseSwissParser.__subclasses__():
            yield parser_class(data_file)

    @api.model
    def _create_bank_statement(self, stmt_vals):
        """Override to support attachement
        """
        attachments = list(stmt_vals.pop('attachments', list()))

        statement_id, notifs = super(
            AccountBankStatementImport,
            self
        )._create_bank_statement(
            stmt_vals
        )
        for attachment in attachments:
            att_data = {
                'name': attachment[0],
                'type': 'binary',
                'datas': attachment[1],
            }
            statement_line = self.env[
                'account.bank.statement.line'].search(
                    [('ref', '=', attachment[0])]
                )
            if statement_line:
                # Link directly attachement with the right statement line
                att_data['res_id'] = statement_line.id
                att_data['res_model'] = 'account.bank.statement.line'
                att = self.env['ir.attachment'].create(att_data)
                statement_line.related_files |= att
            else:
                att_data['res_id'] = statement_id
                att_data['res_model'] = 'account.bank.statement'
                att = self.env['ir.attachment'].create(att_data)

        return statement_id, notifs

    @api.model
    def _find_bank_account_id(self, account_number):
        """ Override to find Postfinance account Given IBAN number """
        bank_account_id = super(AccountBankStatementImport, self).\
            _find_bank_account_id(account_number)
        if not bank_account_id and account_number and len(
                account_number) == 21:
            pf_formated_acc_number = account_number[9:].lstrip('0')
            bank_account = self.env['res.partner.bank'].search(
                [('sanitized_acc_number', '=', pf_formated_acc_number)],
                limit=1)
            bank_account_id = bank_account.id
        return bank_account_id
