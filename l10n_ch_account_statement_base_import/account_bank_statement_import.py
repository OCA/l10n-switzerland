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
from .parser import base_parser


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    related_files = fields.Many2many(
        comodel_name='ir.attachment',
        string='Related files',
        readonly=True
    )


class account_bank_statement_import(models.TransientModel):

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
            return super(account_bank_statement_import, self)._parse_file(
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

    def _create_bank_statements(self, stmts_vals):
        """Override to support attachement
        in the long run it should be deprecated by
        https://github.com/OCA/bank-statement-import/issues/25
        """
        statement_ids, notifs = super(
            account_bank_statement_import,
            self
        )._create_bank_statements(
            stmts_vals
        )
        # statements value are sorted list so we received sorted statement_ids
        index = 0
        for st_vals in stmts_vals:
            if 'attachments' in st_vals:
                statement = self.env['account.bank.statement'].browse(
                    statement_ids[index]
                )
                attachments = self.env['ir.attachment'].browse()
                for attach in st_vals['attachments']:
                    attachments += self.env['ir.attachment'].create(
                        {
                            'name': attach[0],
                            'res_model': 'account.bank.statement',
                            'res_id': statement_ids[index],
                            'type': 'binary',
                            'datas': attach[1],
                        }
                    )
                statement.related_files = attachments
                index += 1
        return statement_ids, notifs
