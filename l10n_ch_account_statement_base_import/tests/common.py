# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Emanuel Cino
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
from openerp.modules import get_module_resource


def get_file_content(filename):
    filepath = get_module_resource(
        'l10n_ch_account_statement_base_import',
        'data',
        filename
    )
    with open(filepath) as data_file:
        return data_file.read()


class BaseParserTest(common.TransactionCase):

    def get_file_content(self, filename):
        return get_file_content(filename)


class BaseStatementImportTest(common.TransactionCase):

    def setUp(self):
        super(BaseStatementImportTest, self).setUp()
        self.company_a = self.env.ref('base.main_company')
        currency = self.env.ref('base.CHF')
        self.company_a.write(
            {'currency_id': currency.id}
        )
        self.account_bank_statement_obj = self.env["account.bank.statement"]
        # create the 2002, 2011-2012, 2014 fiscal years since imported
        # test files reference statement lines in those years
        self.create_fiscalyear("2002", self.company_a)
        self.create_fiscalyear("2011", self.company_a)
        self.create_fiscalyear("2012", self.company_a)
        self.create_fiscalyear("2014", self.company_a)
        self.account = self.env.ref("account.a_recv")
        self.journal = self.env.ref("account.bank_journal")
        self.import_wizard_obj = self.env['account.bank.statement.import']

    def create_fiscalyear(self, year, company):
        fiscalyear_obj = self.env["account.fiscalyear"]
        fiscalyear = fiscalyear_obj.create(
            {
                "name": year,
                "code": year,
                "date_start": year + "-01-01",
                "date_stop": year + "-12-31",
                "company_id": company.id
            }
        )
        fiscalyear.create_period3()
        return fiscalyear

    def create_wizard_from_file(self, filename):
        return self.import_wizard_obj.create(
            {'data_file': get_file_content(filename).encode('base64')}
        )
