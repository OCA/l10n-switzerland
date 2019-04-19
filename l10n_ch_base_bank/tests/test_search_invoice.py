# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import common
from odoo.tests.common import Form
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSearchInvoice(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref('base.main_company')
        bank = cls.env['res.bank'].create({
            'name': 'BCV',
            'bic': 'BBRUBEBB',
            'clearing': '234234',
            'ccp': '01-1234-1',
        })
        cls.env['res.partner.bank'].create({
            'partner_id': cls.company.partner_id.id,
            'bank_id': bank.id,
            # 'acc_number': 'Bank/CCP 01-1234-1',
            # else not recognized as a postal account number:
            'acc_number': '01-1234-1',
        })
        cls.partner = cls.env['res.partner'].create(
            {'name': 'Test'}
        )
        cls.bank_journal = cls.env['account.journal'].create({
            'company_id': cls.company.id,
            'type': 'bank',
            'code': 'BNK42',
            'bank_id': bank.id,
            'bank_acc_number': '10-8060-7',
        })

    def new_form(self):
        inv = Form(
            self.env['account.invoice'],
            view='account.invoice_form'
        )
        inv.partner_id = self.partner
        inv.journal_id = self.bank_journal
        inv.type = 'out_invoice'
        inv.reference_type = 'isr'
        return inv

    def assert_find_ref(self, reference, operator, value):
        inv_form = self.new_form()
        inv_form.reference = reference

        invoice = inv_form.save()

        found = self.env['account.invoice'].search(
            [('reference', operator, value)],
        )
        self.assertEqual(invoice, found)

    def assert_not_find_ref(self, reference, operator, value):
        inv_form = self.new_form()
        inv_form.reference = reference
        inv_form.save()

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
        inv_form = self.new_form()
        inv_form.reference = '27 29990 00000 00001 70400 25019'
        invoice = inv_form.save()

        found = self.env['account.invoice'].search(
            [('partner_id', '=', self.partner.id)],
        )
        self.assertEqual(invoice, found)

    def test_search_unary_operator(self):
        inv_form = self.new_form()
        inv_form.reference = '27 29990 00000 00001 70400 25019'
        invoice = inv_form.save()

        found = self.env['account.invoice'].search(
            [('reference', 'like', '2999000000')],
        )
        self.assertEqual(invoice, found)
