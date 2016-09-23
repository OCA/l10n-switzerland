# -*- coding: utf-8 -*-
# Copyright 2016 Open Net Sàrl
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
        self.vat = tax_obj.create({
            'name': 'dummy VAT',
            'price_include': True,
            'amount': 4.2,
            'tax_cresus_mapping': 'VAT'})
        self.reserve = analytic_account_obj.create({
            'name': 'Fortune',
            'code': '10'})

    def test_import(self):
        journal_obj = self.env['account.journal']
        misc = journal_obj.search(
            [('code', '=', 'MISC')], limit=1)
        if not misc:
            misc = journal_obj.create({
                'code': 'MISC',
                'name': 'dummy MISC',
                'type': 'general'})

        def get_path(filename):
            res = get_resource_path('l10n_ch_import_cresus', 'tests', filename)
            return res

        with open(get_path('input.csv')) as src:
            buf = StringIO()
            base64.encode(src, buf)
            contents = buf.getvalue()
            buf.close()

        wizard = self.env['account.cresus.import'].create({
            'journal_id': misc.id,
            'file': contents})
        wizard._import_file()

        res = wizard.imported_move_ids
        res.assert_balanced()

        gold = open(get_path('golden-output.txt'))
        temp = tempfile.NamedTemporaryFile(prefix='odoo-l10n_ch_import_cresus')

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
        gold.close()
        temp.close()
        if len(diff) > 2:
            for i in diff:
                _logger.error(i.rstrip())
            self.fail("actual output doesn't match exptected output")
