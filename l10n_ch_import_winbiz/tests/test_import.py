# -*- coding: utf-8 -*-
# © 2016 Bettens Louis (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.tests.common as common
from openerp.modules import get_module_resource
from StringIO import StringIO
import base64


class TestImport(common.TransactionCase):

    def setUp(self):
        super(TestImport, self).setUp()

        tax_obj = self.env['account.tax']
        account_obj = self.env['account.account']
        analytic_account_obj = self.env['account.analytic.account']

        user_type = self.env['account.account.type'].search(
            [('include_initial_balance', '=', False)], limit=1)
        for code in ['1000', '1010', '1210', '2200', '2800', '2915', '6512',
                     '6513', '6642', '9100', '10101']:
            found = account_obj.search([('code', '=', code)])
            if found:  # patch it within the transaction
                found.user_type_id = user_type.id
            else:
                account_obj.create({
                    'name': 'dummy %s' % code,
                    'code': code,
                    'user_type_id': user_type.id,
                    'reconcile': True})

    def test_import(self):
        journal_obj = self.env['account.journal']
        misc = journal_obj.search(
            [('name', 'ilike', 'miscellaneous')], limit=1)

        test_file_path = get_module_resource('l10n_ch_import_winbiz',
                                             'tests',
                                             'winbiz.xls')
        buf = StringIO()
        with open(test_file_path) as f:
            base64.encode(f, buf)
        contents = buf.getvalue()
        buf.close()
        wizard = self.env['account.winbiz.import'].create({
            'journal_id': misc.id,
            'file': contents})
        wizard.import_file()

        res = wizard.imported_move_ids
        res.assert_balanced()
