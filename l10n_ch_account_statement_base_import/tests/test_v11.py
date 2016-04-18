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
from ..parsers.v11_file_parser import V11Parser
from .common import BaseParserTest, BaseStatementImportTest


class V11ParserTest(BaseParserTest):

    def setUp(self):
        super(BaseParserTest, self).setUp()
        self.parser = V11Parser(
            self.get_file_content('vesr.V11')
        )

    def test_file_type_detection(self):
        """Test file type detection"""
        self.assertTrue(self.parser.file_is_known())
        self.parser.lines = ['BING']
        self.assertFalse(self.parser.file_is_known())

    def test_parse(self):
        """Test file is correctly parsed"""
        self.parser.parse()
        self.assertEqual('CHF',
                         self.parser.get_currency())
        statements = self.parser.get_statements()
        self.assertIsInstance(statements, list)
        self.assertEqual(len(statements), 1)
        self.assertTrue(all(isinstance(x, dict) for x in statements))
        statement = statements[0]
        self.assertTrue(
            all(isinstance(x, dict)for x in statement['transactions']))
        self.assertEqual(0.00, statement['balance_start'])
        self.assertEqual(3820.00, statement['balance_end_real'])
        self.assertEqual(27, len(statement['transactions']))
        st_line_obj = statement['transactions'][0]
        # Read common infos of first line
        self.assertEqual(st_line_obj['date'], "2012-11-15")
        self.assertEqual(st_line_obj['amount'], 65.00)
        self.assertEqual(st_line_obj['ref'], "000000000000000264200013592")

# here you can add more subtle and detailed test
# for each _parse functions using forged element tree


class V11ImportTest(BaseStatementImportTest):

    def setUp(self):
        super(V11ImportTest, self).setUp()
        self.import_wizard_obj = self.import_wizard_obj.with_context(
            journal_id=self.journal.id)

    def test_v11_import(self):
        """Test if V11 statement is correct"""
        wizard = self.create_wizard_from_file('vesr.V11')
        action = wizard.import_file()
        statements = self.env['account.bank.statement'].browse(
            action['context'].get('statement_ids')
        )
        statement = statements[0]
        self.assertEqual(0.00, statement.balance_start)
        self.assertEqual(3820.00, statement.balance_end_real)
        self.assertEqual(27, len(statement.line_ids))
        # self.assertTrue(statement.account_id)
        self.assertEqual(0, len(statement.mapped('line_ids.related_files')))
        st_line = statement.line_ids[0]
        # Read common infos of first line
        self.assertEqual(st_line.date, "2012-11-15")
        self.assertEqual(st_line.amount, 65.00)
        self.assertEqual(st_line.ref, "000000000000000264200013592")
