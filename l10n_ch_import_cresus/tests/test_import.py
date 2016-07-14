# -*- coding: utf-8 -*-
# © 2016 Bettens Louis (Open Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.tests.common as common
from base64 import b64encode
import logging

_logger = logging.getLogger(__name__)


class TestImport(common.TransactionCase):

    def setUp(self):
        super(TestImport, self).setUp()

        tax_obj = self.env['account.tax']
        account_obj = self.env['account.account']
        analytic_account_obj = self.env['account.analytic.account']

        user_type = self.env['account.account.type'].search([('include_initial_balance', '=', False)], limit=1)
        for code in '1000 1010 1210 2200 2800 2915 6512 6513 6642 9100'.split():
            found = account_obj.search([('code', '=', code)])
            if found: # patch it within the transaction
                found.user_type_id = user_type.id
            else:
                account_obj.create({
                    'name': 'dummy %s' % code,
                    'code': code,
                    'user_type_id': user_type.id,
                    'reconcile': True})
        self.vat = tax_obj.create({'name': 'dummy VAT', 'price_include': True, 'amount': 4.2, 'tax_cresus_mapping': 'VAT'})
        self.reserve = analytic_account_obj.create({
            'name': 'Fortune',
            'code': '10'})

    def test_import(self):
        journal_obj = self.env['account.journal']
        account_obj = self.env['account.account']
        move_obj = self.env['account.move']

        wizard = self.env['account.cresus.import'].create({
            'journal_id': journal_obj.search([('name', 'ilike', 'miscellaneous')], limit=1).id,
            'file': b64encode('''\
01.01.02	1000	9100		Solde à nouveau Caisse	1'000.00			10
01.01.02	1010	9100		Solde à nouveau CCP	8'000.00			10
01.01.02	1210	9100		Solde à nouveau Matériel	100'000.00			10
01.01.02	9100	2800		Solde à nouveau Capital	20'000.00			10
01.01.02	9100	2915		Solde à nouveau Réserve générale	323.20			10
07.01.2002	6642	1010	1	Frais de déplacement - Frauenfeld	45.00
07.01.02	6513	1010	2	Frais de prospection - Tartempion	218.50
12.01.02	6642	1010	3	Frais de déplacement - Tolochenaz	15.00
14.01.02	6512	...	4	Salt, (TVA) net, TVA = 13.17	173.38
14.01.02	2200	...	4	Salt, 7.6% de TVA (TVA)	13.17	VAT
14.01.02	...	1010	4	Salt Total, (TVA)	186.55
''')})
        data = wizard._parse_csv()
        data = wizard._standardise_data(data)
        data = [[row[field] for field in wizard.HEAD_ODOO] for row in data]
        res = move_obj.load(wizard.HEAD_ODOO, data)
        wizard._manage_load_results(res)

        self.assertEqual(wizard.report, 'Lines imported')
        res = move_obj.browse(wizard.imported_move_ids.ids)
        self.assertEqual(len(res), 5)
        self.assertEqual(res[1].date, '2002-01-07')
        self.assertEqual(res[2].date, '2002-01-07')
        res.assert_balanced()
        for l in res[0].line_ids:
            self.assertEqual(l.analytic_account_id, self.reserve)
        self.assertEqual(res[4].line_ids[1].tax_line_id, self.vat)
