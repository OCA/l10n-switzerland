# -*- coding: utf-8 -*-
# © 2016 Bettens Louis (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.tests.common as common
from openerp.modules import get_resource_path
import logging
from StringIO import StringIO
import base64
from pprint import pprint
import difflib
import tempfile
import os

_logger = logging.getLogger(__name__)

MOVE_UNIVERSAL_FIELDS = {'name', 'ref', 'date', 'journal_id', 'currency_id', 'rate_diff_partial_rec_id', 'state', 'line_ids', 'partner_id', 'amount', 'narration', 'company_id', 'matched_percentage', 'statement_line_id', 'dummy_account_id'}

LINE_UNIVERSAL_FIELDS = {'name', 'quantity', 'product_uom_id', 'product_id', 'debit', 'credit', 'balance', 'debit_cash_basis', 'credit_cash_basis', 'balance_cash_basis', 'amount_currency', 'company_currency_id', 'currency_id', 'amount_residual', 'amount_residual_currency', 'account_id', 'move_id', 'narration', 'ref', 'payment_id', 'statement_id', 'reconciled', 'matched_debit_ids', 'matched_credit_ids', 'journal_id', 'blocked', 'date_maturity', 'date', 'analytic_line_ids', 'tax_ids', 'tax_line_id', 'analytic_account_id', 'company_id', 'counterpart', 'invoice_id', 'partner_id', 'user_type_id'}

class TestImport(common.TransactionCase):

    def setUp(self):
        super(TestImport, self).setUp()

        tax_obj = self.env['account.tax']
        account_obj = self.env['account.account']
        analytic_account_obj = self.env['account.analytic.account']

        user_type = self.env['account.account.type'].search(
            [('include_initial_balance', '=', False)], limit=1)

        self.account_codes = {}
        for code in ['1000', '1010', '1020', '1050', '1061', '1120', '2000',
                     '2010', '2091', '2200', '4000', '4051', '4055', '4095',
                     '4210', '4300', '4400', '4412', '4510', '4511', '4590',
                     '4600', '5472', '5700', '6200', '6207', '8100']:
            acc = account_obj.search([('code', '=', code)])
            if acc:  # patch it within the transaction
                acc.user_type_id = user_type.id
            else:
                acc = account_obj.create({
                    'name': 'dummy %s' % code,
                    'code': code,
                    'user_type_id': user_type.id,
                    'reconcile': True})
            self.account_codes[acc.id] = acc.code

    def test_import(self):
        journal_obj = self.env['account.journal']
        for i in 'BILL', 'MISC', 'STJ', 'OJ', 'JS', 'INV':
            if not journal_obj.search([('code', '=', i)]):
                journal_obj.create({'name': 'dummy '+i, 'code': i, 'type':'general'})

        def get_path(filename):
            res = get_resource_path('l10n_ch_import_winbiz', 'tests', filename)
            return res
        input = open(get_path('input.xls'))
        gold = open(get_path('golden-output.txt'))
        temp = tempfile.NamedTemporaryFile(prefix='odoo-l10n_ch_import_winbiz',
                                           delete=False)

        buf = StringIO()
        base64.encode(input, buf)
        contents = buf.getvalue()
        buf.close()

        wizard = self.env['account.winbiz.import'].create({
            'file': contents})
        wizard._import_file()

        res = wizard.imported_move_ids
        res.assert_balanced()

        # Get a predictable representation that can be compared across runs
        data = res.copy_data()
        for mv in data:
            for f in mv.keys():
                if f not in MOVE_UNIVERSAL_FIELDS:
                    del mv[f]
            mv['journal_id'] = journal_obj.browse(mv['journal_id']).code
            for _, _, ln in mv['line_ids']:
                for f in ln.keys():
                    if f not in LINE_UNIVERSAL_FIELDS:
                        del ln[f]
                del ln['move_id']
                ln['account_id'] = self.account_codes[ln['account_id']]
        pprint(data, temp)
        temp.seek(0)
        diff = list(difflib.unified_diff(gold.readlines(), temp.readlines(),
                                         gold.name,        temp.name))
        if len(diff) > 2:
            for i in diff:
                _logger.error(i)
            self.fail("actual output doesn't match exptected output")
        os.remove(temp.name) # intentionally keep it in case of test failure
