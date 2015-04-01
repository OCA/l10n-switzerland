# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
import base64
from openerp.modules import get_module_resource
import openerp.tests.common as test_common


class TestV11import(test_common.TransactionCase):

    def test_file_parsing(self):
        v11_path = get_module_resource('l10n_ch_payment_slip',
                                       'tests',
                                       'test_v11_files',
                                       'test1.v11')
        with open(v11_path) as v11_file:
            importer = self.env['v11.import.wizard'].create(
                {'v11file': base64.encodestring(v11_file.read())}
            )
            v11_file.seek(0)
            lines = v11_file.readlines()
            records = importer._parse_lines(lines)
            self.assertTrue(len(records), 1)
            record = records[0]
            self.assertEqual(
                record,
                {'date': '2022-10-17',
                 'amount': 5415.0,
                 'cost': 0.0,
                 'reference': '005095000000000000000000013'}
            )

    def test_statement_import(self):
        statement = self.env['account.bank.statement'].create(
            {
                'journal_id': self.env.ref('account.bank_journal_usd').id,
            }
        )
        importer_model = self.env['v11.import.wizard'].with_context(
            active_id=statement.id
        )
        v11_path = get_module_resource('l10n_ch_payment_slip',
                                       'tests',
                                       'test_v11_files',
                                       'test1.v11')
        with open(v11_path) as v11_file:
            importer = importer_model.create(
                {'v11file': base64.encodestring(v11_file.read())}
            )
        importer.import_v11()
        statement.refresh()
        self.assertTrue(len(statement.line_ids), 1)
        line = statement.line_ids[0]
        self.assertEqual(line.name, '005095000000000000000000013')
        self.assertEqual(line.ref, '/')
        self.assertEqual(line.amount, 5415.0)
