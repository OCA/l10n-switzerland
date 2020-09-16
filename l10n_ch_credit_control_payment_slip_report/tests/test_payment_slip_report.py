# -*- coding: utf-8 -*-
from odoo.tests.common import SavepointCase


class TestPaymentSlipReport(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestPaymentSlipReport, cls).setUpClass()
        cls.account = cls.env['account.account'].create({
            'code': "1111",
            'name': "Test",
            'user_type_id': cls.env.ref('account.data_account_type_receivable').id,
            'reconcile': True,
        })

    def make_bank(self):
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        bank = self.env['res.bank'].create(
            {
                'name': 'BCV',
                'ccp': '01-1234-1',
                'bic': '23423412',
                'clearing': '23423412',
            }
        )
        bank_account = self.env['res.partner.bank'].create(
            {
                'partner_id': partner.id,
                'owner_name': partner.name,
                'street': partner.street,
                'city': partner.city,
                'zip': partner.zip,
                'state': 'bvr',
                'bank': bank.id,
                'bank_name': bank.name,
                'bank_bic': bank.bic,
                'acc_number': 'R 12312123',
                'bvr_adherent_num': '1234567',
                'print_bank': True,
                'print_account': True,
                'print_partner': True,
            }
        )
        return bank_account

    def make_invoice(self):
        bank_account = self.make_bank()
        invoice = self.env['account.invoice'].create(
            {
                'partner_id': self.env.ref('base.res_partner_12').id,
                'reference_type': 'none',
                'name': 'A customer invoice',
                'account_id': self.account.id,
                'type': 'out_invoice',
                'partner_bank_id': bank_account.id,
            }
        )

        self.env['account.invoice.line'].create(
            {
                'product_id': False,
                'quantity': 1,
                'price_unit': 862.50,
                'invoice_id': invoice.id,
                'name': 'product that cost 862.50 all tax included',
                'account_id': self.account.id,
            }
        )
        invoice.action_invoice_open()
        self.assertTrue(invoice.move_id)
        self.assertEqual(invoice.amount_total, 862.50)
        return invoice

    def test_amount_with_fees(self):
        """Test that dunning fees are included in payment slip's amount"""
        invoice = self.make_invoice()
        move_line = invoice.move_id.line_ids[0]
        self.assertTrue(len(move_line), 1)

        lvl = self.env.ref('account_credit_control.3_time_1')
        credit_line = self.env['credit.control.line'].create(
            {'move_line_id': move_line.id,
             'date_due': '2000-01-01',
             'partner_id': self.env.ref('base.res_partner_12').id,
             'channel': 'email',
             'date': '2000-01-01',
             'balance_due': 100.00,
             'amount_due': 100.00,
             'policy_level_id': lvl.id,
             'state': 'to_be_sent'}
        )
        slip = self.env['l10n_ch.payment_slip'].with_context(
            slip_credit_control_line_id=credit_line.id
        ).create({
            'invoice_id': invoice.id,
            'move_line_id': move_line.id
        })
        self.assertEqual(slip.amount_total, 862.50)
        credit_line.dunning_fees_amount = 30000

        self.env.context = dict(
            self.env.context,
            slip_credit_control_line_id=credit_line.id
        )
        self.assertEqual(slip._compute_amount_hook(), 30862.50)

    def test_printing(self):
        """Test that we can print the report"""
        invoice = self.make_invoice()
        move_line = invoice.move_id.line_ids[0]
        self.assertTrue(len(move_line), 1)

        lvl = self.env.ref('account_credit_control.3_time_1')
        credit_line = self.env['credit.control.line'].create(
            {'move_line_id': move_line.id,
             'date_due': '2000-01-01',
             'partner_id': self.env.ref('base.res_partner_12').id,
             'channel': 'email',
             'date': '2000-01-01',
             'balance_due': 100.00,
             'amount_due': 100.00,
             'policy_level_id': lvl.id,
             'state': 'to_be_sent'}
        )
        report_name = 'slip_from_credit_control'
        report_obj = self.env['report'].with_context(
            active_ids=credit_line.ids)
        return report_obj.get_action(credit_line, report_name)
