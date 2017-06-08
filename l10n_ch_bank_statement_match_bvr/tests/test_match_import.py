# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import collections

from openerp.tests.common import TransactionCase
from openerp.tools.misc import file_open


DATA_DIR = 'l10n_ch_bank_statement_match_bvr/test_files/'
TESTFILE = DATA_DIR + 'test_match_import.pydata'

# Constants that correspond to TESTFILE's contents
ACCOUNT_NUMBER = u'CH1111000000123456789'
Invoice = collections.namedtuple('Invoice', 'bvr_ref amount')
OPEN_INVOICES = [
    Invoice(u'302388292000011111111111111', 2187),
    Invoice(u'302388292000022222222222222', 1296),
]


class TestMatchImport(TransactionCase):
    """simulate a wizard import and check if lines are matched correctly."""
    def setUp(self):
        super(TestMatchImport, self).setUp()
        bank = self.env['res.partner.bank'].create({
            'acc_number': ACCOUNT_NUMBER,
            'partner_id': self.env.ref('base.main_partner').id,
            'company_id': self.env.ref('base.main_company').id,
            'bank_id': self.env.ref('base.res_bank_1').id,
        })
        receivable_type = self.env.ref('account.data_account_type_receivable')
        account = self.env['account.account'].create({
            'reconcile': True,
            'user_type_id': receivable_type.id,          # checked by match_ref
            'code': 'TEST_BNKMBVR',
            'name': u'Receivable account - (test match bvr)',
        })
        journal = self.env['account.journal'].create({
            'type': 'sale',                                      # also checked
            'code': 'TEST_BNKMBVR',
            'name': u'Sales Journal - (test match bvr)',
            'bank_account_id': bank.id,
        })
        self.partner_ids = []
        for n, inv in enumerate(OPEN_INVOICES):
            partner = self.env['res.partner'].create({
                'name': u'Partner %d - (test match bvr)' % n,
            })
            invoice = self.env['account.invoice'].create({
                'partner_id': partner.id,
                'account_id': account.id,
                })
            invoice.number = 'TEST%d%d%d%d' % (n, n, n, n)  # must be non-empty
            line = self.env['account.move.line'].create({
                'name': 'test line',
                'account_id': account.id,
                'invoice_id': invoice.id,
                'journal_id': journal.id,
                'partner_id': partner.id,
                'transaction_ref': inv.bvr_ref,                    # must match
                'amount': inv.amount,
            })
            line.reconciled = False                              # also checked
            self.partner_ids.append(partner.id)

    def test_statement_match(self):
        statement_obj = self.env['account.bank.statement']
        pydata_importer_obj = self.env[
            'l10n_ch_bank_statement_match_bvr.tests.pydata_importer']
        with file_open(TESTFILE) as testfile:
            action = pydata_importer_obj.create({
                'data_file': base64.b64encode(testfile.read()),
            }).import_file()
        stmts = statement_obj.browse(action['context']['statement_ids'])
        lines = stmts.mapped('line_ids')
        res = [(line.partner_id.id, line.name, line.amount) for line in lines]
        self.assertItemsEqual(res, zip(self.partner_ids, *zip(*OPEN_INVOICES)))
