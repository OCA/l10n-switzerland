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
from openerp.tests import common
from ..parsers.postfinance_file_parser import XMLPFParser
from ..parsers.g11_file_parser import G11Parser
from ..parsers.raiffeisen_file_parser import RaffeisenCSVParser
from ..parsers.ubs_file_parser import UBSCSVParser
from ..parsers.v11_file_parser import V11Parser


class BaseSwissImporterTest(common.TransactionCase):

    def test_get_parser(self):
        """Test that parsers are correctly detected"""
        importer_model = self.env['account.bank.statement.import']
        parsers = [x for x in importer_model._get_parsers('dummy_data')]
        self.assertEqual(len(parsers), 5)
        self.assertTrue(any(isinstance(x, XMLPFParser) for x in parsers))
        self.assertTrue(any(isinstance(x, G11Parser) for x in parsers))
        self.assertTrue(
            any(isinstance(x, RaffeisenCSVParser) for x in parsers))
        self.assertTrue(any(isinstance(x, UBSCSVParser) for x in parsers))
        self.assertTrue(any(isinstance(x, V11Parser) for x in parsers))
        # add other parser detection below
