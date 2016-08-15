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
        journal_obj = self.env['account.journal']

        user_type = {}
        for include_initial_balance in False, True:
            user_type[include_initial_balance] = \
                self.env['account.account.type'].create({
                    'include_initial_balance': include_initial_balance,
                    'name': 'dummy'})

        for code, include_initial_balance in [
                ('1000', True),
                ('1010', True),
                ('1020', True),
                ('1050', True),
                ('1061', True),
                ('1120', True),
                ('2000', True),
                ('2010', True),
                ('2091', True),
                ('2200', True),
                ('4000', False),
                ('4051', False),
                ('4055', False),
                ('4095', False),
                ('4210', False),
                ('4300', False),
                ('4400', False),
                ('4412', False),
                ('4510', False),
                ('4511', False),
                ('4590', False),
                ('4600', False),
                ('5472', False),
                ('5700', False),
                ('6200', False),
                ('6207', False),
                ('8100', False),
                ]:
            acc = account_obj.search([('code', '=', code)])
            if acc:
                account_obj.write({
                    'user_type_id': user_type[include_initial_balance].id,
                    'reconcile': True})
            else:
                account_obj.create({
                    'name': 'dummy %s' % code,
                    'code': code,
                    'user_type_id': user_type[include_initial_balance].id,
                    'reconcile': True})

        for code, winbiz_code in [
                ('INV', 'v'),
                ('BILL', 'a'),
                ('OJ', 'o'),
                ('JS', 's'),
                ('MISC', 'd')]:
            journal = journal_obj.search([('code', '=', code)])
            if journal:
                journal.write({
                    'winbiz_mapping': winbiz_code})
            else:
                journal_obj.create({
                    'code': code,
                    'name': 'dummy '+code,
                    'type': 'general',
                    'winbiz_mapping': winbiz_code})

        for code, amount, scope in [
                ('310', 6.5, 'sale'), ('315', 6.5, 'purchase'),
                ('400', 7.5, 'sale'), ('405', 7.5, 'purchase'),
                ('410', 7.6, 'sale'), ('415', 7.6, 'purchase')]:
            tax_obj.create({
                'name': code,
                'amount': amount,
                'type_tax_use': scope,
                'price_include': True})

    def _test_import(self, input_file, input_format):
        def get_path(filename):
            res = get_resource_path('l10n_ch_import_winbiz', 'tests', filename)
            return res

        with open(get_path(input_file)) as src:
            buf = StringIO()
            base64.encode(src, buf)
            contents = buf.getvalue()
            buf.close()

        wizard = self.env['account.winbiz.import'].create({
            'enable_account_based_line_merging': True,
            'file': contents,
            'file_format': input_format})
        wizard._import_file()

        res = wizard.imported_move_ids
        res.assert_balanced()

        gold = open(get_path('golden-output.txt'))
        temp = tempfile.NamedTemporaryFile(prefix='odoo-l10n_ch_import_winbiz')

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
                if ln.tax_ids:
                    p(u"      taxes = (‘%s’)" % u"’, ‘".join(
                        ln.tax_ids.mapped('name')))
        temp.seek(0)
        diff = list(difflib.unified_diff(gold.readlines(), temp.readlines(),
                                         gold.name,        temp.name))
        if len(diff) > 2:
            for i in diff:
                _logger.error(i.rstrip())
            self.fail("actual output doesn't match exptected output")

    def test_import_xls(self):
        self._test_import('input.xls', 'xls')

    def test_import_xml_element_oriented(self):
        self._test_import('input.element-oriented.xml', 'xml')

    def test_import_xml_attribute_oriented(self):
        self._test_import('input.attribute-oriented.xml', 'xml')

    def test_import_xml_raw_attribute_oriented(self):
        self._test_import('input.attribute-oriented.raw.xml', 'xml')
