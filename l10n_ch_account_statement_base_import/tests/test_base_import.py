# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino
#    Copyright 2014 Compassion Suisse
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
import inspect
import os
from openerp.tests import common


class l10n_ch_import(common.TransactionCase):

    def setUp(self):
        super(l10n_ch_import, self).setUp()
        self.company_a = self.browse_ref('base.main_company')
        # Define the currency to CHF
        currency_id = self.registry('res.currency').search(
            self.cr, self.uid, [('name', '=', 'CHF')])[0]
        self.registry('res.company').write(self.cr, self.uid, self.company_a.id, {
            'currency_id': currency_id
        })
        self.profile_obj = self.registry("account.statement.profile")
        self.account_bank_statement_obj = self.registry(
            "account.bank.statement")
        # create the 2002, 2011-2012 fiscal years since imported test files reference
        # statement lines in those years
        self.fiscalyear_id = self._create_fiscalyear("2002", self.company_a.id)
        self.fiscalyear_id = self._create_fiscalyear("2011", self.company_a.id)
        self.fiscalyear_id = self._create_fiscalyear("2012", self.company_a.id)
        self.account_id = self.ref("account.a_recv")
        self.journal_id = self.ref("account.bank_journal")
        self.import_wizard_obj = self.registry('credit.statement.import')

    def _create_fiscalyear(self, year, company_id):
        fiscalyear_obj = self.registry("account.fiscalyear")
        fiscalyear_id = fiscalyear_obj.create(self.cr, self.uid, {
            "name": year,
            "code": year,
            "date_start": year + "-01-01",
            "date_stop": year + "-12-31",
            "company_id": company_id
        })
        fiscalyear_obj.create_period3(self.cr, self.uid, [fiscalyear_id])
        return fiscalyear_id

    def _filename_to_abs_filename(self, file_name):
        dir_name = os.path.dirname(inspect.getfile(self.__class__))
        return os.path.join(dir_name, file_name)
        
    def _create_statement_profile(self, import_type):
        self.profile_id = self.profile_obj.create(self.cr, self.uid, {
            "name": "BASE_PROFILE",
            "commission_account_id": self.account_id,
            "journal_id": self.journal_id,
            "import_type": import_type})

    def _import_file(self, file_name):
        """ import a file using the wizard
        return the create account.bank.statement object
        """
        with open(file_name) as f:
            content = f.read()
            wizard_id = self.import_wizard_obj.create(self.cr, self.uid, {
                "profile_id": self.profile_id,
                'input_statement': base64.b64encode(content),
                'file_name': os.path.basename(file_name),
            })
            res = self.import_wizard_obj.import_statement(
                self.cr, self.uid, wizard_id)
            statement_id = self.account_bank_statement_obj.search(
                self.cr, self.uid, eval(res['domain']))
            return self.account_bank_statement_obj.browse(
                self.cr, self.uid, statement_id)[0]

    def test_postfinance_xml(self):
        """Test import from xml
        """
        self._create_statement_profile("pf_xmlparser")
        file_name = self._filename_to_abs_filename(
            os.path.join("..", "data", "postfinance_xml.tar.gz"))
        statement = self._import_file(file_name)
        
        # Validate imported statement
        self.assertEqual("/", statement.name)
        self.assertEqual(372797.79, statement.balance_start)
        self.assertEqual(372982.55, statement.balance_end_real)
        self.assertEqual(22, len(statement.line_ids))
        self.assertTrue(statement.account_id)
        st_line_obj = statement.line_ids[0]
        # Read common infos of first line
        self.assertEqual(st_line_obj.date, "2011-03-28")
        self.assertEqual(st_line_obj.amount, -227.30)
        self.assertEqual(st_line_obj.name, "ZAHLUNGSAUFTRAG NR. 30002102")
        
    def test_v11_esr_file(self):
        """Test import from v11 file
        """
        self._create_statement_profile("esr_fileparser")
        file_name = self._filename_to_abs_filename(
            os.path.join("..", "data", "vesr.V11"))
        statement = self._import_file(file_name)

        # Validate imported statement
        self.assertEqual("/", statement.name)
        self.assertEqual(3820.00, statement.balance_end_real)
        self.assertEqual(0.00, statement.balance_start)
        self.assertEqual(27, len(statement.line_ids))
        self.assertTrue(statement.account_id)
        st_line_obj = statement.line_ids[0]
        # Read common infos of first line
        self.assertEqual(st_line_obj.date, "2012-11-16")
        self.assertEqual(st_line_obj.amount, 65.00)
        self.assertEqual(st_line_obj.ref, "000000000000000264200013592")
        
    def test_raiffeisen_detailed_file(self):
        """Test import from raiffeisen detailed csv file
        """
        self._create_statement_profile("raiffeisen_details_csvparser")
        file_name = self._filename_to_abs_filename(
            os.path.join("..", "data", "raiffeisen_details.csv"))
        statement = self._import_file(file_name)

        # Validate imported statement
        self.assertEqual("/", statement.name)
        self.assertEqual(535.05, statement.balance_end_real)
        self.assertEqual(10, len(statement.line_ids))
        self.assertTrue(statement.account_id)
        st_line_obj = statement.line_ids[0]
        # Read common infos of first line
        self.assertEqual(st_line_obj.date, "2014-08-06")
        self.assertEqual(st_line_obj.amount, 50.00)
        self.assertEqual(st_line_obj.name, "Customer1 1/1202 GENEVE 6/CH/UBS/XXXX-XXXXXXXX COTISATION MENSUELLE ")
        
    def test_ubs_file(self):
        """Test import from ubs csv file
        """
        self._create_statement_profile("ubs_csvparser")
        file_name = self._filename_to_abs_filename(
            os.path.join("..", "data", "UBS_export.csv"))
        statement = self._import_file(file_name)

        # Validate imported statement
        self.assertEqual("/", statement.name)
        self.assertEqual(20827.00, statement.balance_end_real)
        self.assertEqual(20289.60, statement.balance_start)
        self.assertEqual(6, len(statement.line_ids))
        self.assertTrue(statement.account_id)
        st_line_obj = statement.line_ids[0]
        # Read common infos of first line
        self.assertEqual(st_line_obj.date, "2014-08-02")
        self.assertEqual(st_line_obj.amount, 236.10)
        self.assertEqual(st_line_obj.name, "Dividend VN   472672     101368S3 NOKIA")
        
    def test_g11_file(self):
        """Test import from g11 file
        """
        self._create_statement_profile("g11_fileparser")
        file_name = self._filename_to_abs_filename(
            os.path.join("..", "data", "aus_dd_esr.g11"))
        statement = self._import_file(file_name)

        # Validate imported statement
        self.assertEqual("/", statement.name)
        self.assertEqual(951.25, statement.balance_end_real)
        self.assertEqual(0.00, statement.balance_start)
        self.assertEqual(6, len(statement.line_ids))
        self.assertTrue(statement.account_id)
        st_line_obj = statement.line_ids[0]
        # Read common infos of first line
        self.assertEqual(st_line_obj.date, "2002-10-29")
        self.assertEqual(st_line_obj.amount, -315.05)
        self.assertEqual(st_line_obj.name, "Debtor protestation.")
        self.assertEqual(st_line_obj.ref, "116149669100029449230099856")
