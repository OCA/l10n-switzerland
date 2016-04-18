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
import re
from ..parsers.postfinance_file_parser import XMLPFParser
from .common import BaseParserTest, BaseStatementImportTest


class PFXMLParserTest(BaseParserTest):

    def setUp(self):
        super(BaseParserTest, self).setUp()
        self.parser = XMLPFParser(
            self.get_file_content('postfinance_xml.tar.gz')
        )

    def test_file_uncompress(self):
        """Test that tar file is uncompressed correctly"""
        self.assertTrue(
            re.search(r'\<IC_HEADER',
                      self.parser.data_file)
        )

    def test_parser_can_open_non_tar(self):
        """Test that non compressed file can be read"""
        raw = """<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE IC SYSTEM "acc_200.dtd">
<?xml-stylesheet type="text/xsl" href="acc_200.xsl"?>
<IC xmlns:PF="http://www.post.ch/xml"><IC_HEADER></IC_HEADER></IC>"""
        parser = XMLPFParser(raw)
        self.assertEqual(parser.data_file, raw)

    def test_file_type_detection(self):
        """Test file type detection"""
        self.assertTrue(self.parser.file_is_known())
        self.parser.data_file = 'BANG'
        self.assertFalse(self.parser.file_is_known())

    def test_parse(self):
        """Test file is correctly parsed"""
        self.parser.parse()
        self.assertEqual('250090342',
                         self.parser.get_account_number())
        self.assertEqual('CHF',
                         self.parser.get_currency())
        statements = self.parser.get_statements()
        self.assertIsInstance(statements, list)
        self.assertEqual(len(statements), 1)
        self.assertTrue(all(isinstance(x, dict) for x in statements))
        statement = statements[0]
        self.assertTrue(
            all(isinstance(x, dict)for x in statement['transactions']))
        self.assertEqual(372797.79, statement['balance_start'])
        self.assertEqual(372982.55, statement['balance_end_real'])
        self.assertEqual(22, len(statement['transactions']))
        first_transaction = {
            'unique_import_id': '20110322001201000200001000000101',
            'ref': '20110322001201000200001000000101',
            'partner_name': None,
            'note': None,
            'amount': -227.3,
            'account_number': None,
            'date': '2011-03-28',
            'name': 'ZAHLUNGSAUFTRAG NR. 30002102'
        }
        self.assertEqual(first_transaction, statement['transactions'][0])

    def test_attachement_extraction(self):
        """Test if scan are extracted correctly"""
        self.assertEqual(
            set(['20110404001203000100002', '20110407001203000200002']),
            set(self.parser.attachments.keys())
        )


class PostFinanceImportTest(BaseStatementImportTest):

    def setUp(self):
        super(PostFinanceImportTest, self).setUp()
        self.env['res.partner.bank'].create(
            {'footer': False,
             'company_id': self.company_a.id,
             'bank_name': 'test postfinance import',
             'state': 'bank',
             'acc_number': 250090342,
             'partner_id': self.company_a.partner_id.id,
             'journal_id': self.journal.id}
        )
        self.import_wizard_obj = self.import_wizard_obj.with_context(
            journal_id=self.journal.id)

    def test_postfinance_xml_import(self):
        """Test if postfinance statement is correct"""
        wizard = self.create_wizard_from_file('postfinance_xml.tar.gz')
        action = wizard.import_file()
        statements = self.env['account.bank.statement'].browse(
            action['context'].get('statement_ids')
        )
        statement = statements[0]
        self.assertEqual(372797.79, statement.balance_start)
        self.assertEqual(372982.55, statement.balance_end_real)
        self.assertEqual(22, len(statement.line_ids))
        self.assertTrue(statement.account_id)
        self.assertEqual(2, len(statement.mapped('line_ids.related_files')))
        st_line = statement.line_ids[0]
        # Read common infos of first line
        self.assertEqual(st_line.date, "2011-03-28")
        self.assertEqual(st_line.amount, -227.30)
        self.assertEqual(st_line.name, "ZAHLUNGSAUFTRAG NR. 30002102")
        self.assertEqual(st_line.ref, "20110322001201000200001000000101")
