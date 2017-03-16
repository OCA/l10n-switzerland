# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests import common


class TestSearchInvoice(common.TransactionCase):

    def setUp(self):
        super(TestSearchInvoice, self).setUp()
        self.company = self.env.ref('base.main_company')
        bank = self.env['res.bank'].create({
            'name': 'BCV',
            'bic': 'BIC23423',
            'clearing': '234234',
            'ccp': '01-1234-1',
        })
        bank_account = self.env['res.partner.bank'].create({
            'partner_id': self.company.partner_id.id,
            'bank_id': bank.id,
            'acc_number': 'Bank/CCP 01-1234-1',
        })
        self.company.partner_id.bank_ids = bank_account
        self.partner = self.env['res.partner'].create(
            {'name': 'Test'}
        )

    def assert_find_ref(self, reference, operator, value):
        values = {
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'reference_type': 'bvr',
            'reference': reference,
        }
        invoice = self.env['account.invoice'].create(values)
        found = self.env['account.invoice'].search(
            [('reference', operator, value)],
        )
        self.assertEqual(invoice, found)

    def assert_not_find_ref(self, reference, operator, value):
        values = {
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'reference_type': 'bvr',
            'reference': reference,
        }
        self.env['account.invoice'].create(values)
        found = self.env['account.invoice'].search(
            [('reference', operator, value)],
        )
        self.assertFalse(found)

    def test_search_equal_strict(self):
        self.assert_find_ref(
            '27 29990 00000 00001 70400 25019',
            '=', '27 29990 00000 00001 70400 25019'
        )

    def test_search_equal_whitespace_right(self):
        self.assert_not_find_ref(
            '272999000000000017040025019',
            '=', '27 29990 00000 00001 70400 25019'
        )

    def test_search_equal_whitespace_left(self):
        self.assert_not_find_ref(
            '27 29990 00000 00001 70400 25019',
            '=', '272999000000000017040025019'
        )

    def test_search_like_whitespace_right(self):
        self.assert_find_ref(
            '272999000000000017040025019', 'like', '1 70400 25'
        )

    def test_search_like_whitespace_left(self):
        self.assert_find_ref(
            '27 29990 00000 00001 70400 25019', 'like', '17040025'
        )

    def test_search_like_whitespace_both(self):
        self.assert_find_ref(
            '27 29990 00000 00001 70400 25019',
            'like', '17 040025 01'
        )

    def test_search_eqlike_whitespace_raw(self):
        self.assert_not_find_ref(
            '27 29990 00000 00001 70400 25019',
            '=like', '17 040025 01'
        )

    def test_search_eqlike_whitespace_wildcards(self):
        self.assert_find_ref(
            '27 29990 00000 00001 70400 25019',
            '=like', '%17 040025 01%'
        )

    def test_search_different(self):
        self.assert_not_find_ref(
            '27 29990 00000 00001 70400 25019', 'like', '4273473'
        )

    def test_search_other_field(self):
        values = {
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'reference_type': 'bvr',
            'reference': '27 29990 00000 00001 70400 25019',
        }
        invoice = self.env['account.invoice'].create(values)
        found = self.env['account.invoice'].search(
            [('partner_id', '=', self.partner.id)],
        )
        self.assertEqual(invoice, found)

    def test_search_unary_operator(self):
        values = {
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'reference_type': 'bvr',
            'reference': '27 29990 00000 00001 70400 25019',
        }
        invoice = self.env['account.invoice'].create(values)
        found = self.env['account.invoice'].search(
            ['|',
             ('partner_id', '=', False),
             ('reference', 'like', '2999000000'),
             ],
        )
        self.assertEqual(invoice, found)
