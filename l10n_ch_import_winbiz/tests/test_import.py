# -*- coding: utf-8 -*-
# © 2016 Bettens Louis (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.tests.common as common
from openerp.modules import get_resource_path
import logging
from StringIO import StringIO
import base64
import difflib
import tempfile

_logger = logging.getLogger(__name__)


class TestImport(common.TransactionCase):

    def setUp(self):
        super(TestImport, self).setUp()

        tax_obj = self.env['account.tax']
        account_obj = self.env['account.account']
        analytic_account_obj = self.env['account.analytic.account']

        user_type = self.env['account.account.type'].search(
            [('include_initial_balance', '=', False)], limit=1)

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
        for code, amount, scope in [
                ('310', 6.5, 'sale'), ('315', 6.5, 'purchase'),
                ('400', 7.5, 'sale'), ('405', 7.5, 'purchase'),
                ('410', 7.6, 'sale'), ('415', 7.6, 'purchase')]:
            tax_obj.search([('name', '=', code)]).unlink()
            tax_obj.create({'name':code,'amount':amount,'type_tax_use':scope})

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
        temp = tempfile.NamedTemporaryFile(prefix='odoo-l10n_ch_import_winbiz')

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
        def p(u):
            temp.write(u.encode('utf-8'))
            temp.write('\n')

        first = True
        for mv in res:
            if not first:
                p(u"")
            first = False
            p(u"move ‘%s’" % mv.ref)
            p(u"  (dated %s)" % mv.date)
            p(u"  (in journal %s)" % mv.journal_id.code)
            p(u"  with lines:")
            for ln in mv.line_ids:
                p(u"    line “%s”" % ln.name)
                if ln.debit:
                    p(u"      debit = %s" % ln.debit)
                if ln.credit:
                    p(u"      credit = %s" % ln.credit)
                p(u"      account is ‘%s’" % ln.account_id.code)
                if ln.tax_line_id:
                    p(u"      originator tax is ‘%s’" % ln.tax_line_id.name)
        temp.seek(0)
        diff = list(difflib.unified_diff(gold.readlines(), temp.readlines(),
                                         gold.name,        temp.name))
        if len(diff) > 2:
            for i in diff:
                _logger.error(i.rstrip())
            self.fail("actual output doesn't match exptected output")
