# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo.modules import get_module_resource


class TestImportPain002(TransactionCase):

    def import_file_pain002(self):
        test_file_path = get_module_resource('l10n_ch_import_pain002',
                                             'test_files',
                                             'pain002p-rejected.xml')

        file_to_import = open(test_file_path, 'r')
        data = file_to_import.read()
        data = data.replace("\n", "")

        self.account_pain002.parse(data)

    def setUp(self):
        super(TestImportPain002, self).setUp()

        self.invoice_name = 'test invoice pain002'
        self.invoice_line_name = 'test invoice line pain002'
        self.order_name = '2017/1013'
        self.journal_name = '2017/1013'
        self.payment_line_name = 'Ltest'

        self.account_pain002 = self.env['account.pain002.parser']

        # Create payment order from the invoice
        invoice = self.env['account.invoice'].search(
            [('move_name', '=', self.invoice_name)])

        # Validate the invoice
        invoice.action_invoice_open()

        # Create a payment order
        action = invoice.create_account_payment_line()
        payment_order_id = action['res_id']

        payment_order = self.env['account.payment.order'].search(
            [('id', '=', payment_order_id)])

        partner_bank = self.env['account.journal'].search(
            [('name', '=', self.journal_name)])

        bank = self.env['account.journal'].search([('name', '=', 'Bank')])

        payment_order.name = self.order_name
        bank.update_posted = True

        payment_order.journal_id = partner_bank.id
        # Confirm payment order
        payment_order.draft2open()
        # Generate payment file
        payment_order.open2generated()
        # File successfully uploaded
        payment_order.generated2uploaded()

        # Adapt payment line to mach with the pain002 file
        payment_line = self.env['bank.payment.line'].search(
            [('order_id', '=', payment_order.id)])

        payment_line.name = self.payment_line_name

        # self.env.cr.commit()

    def test_invoice_exist(self):
        invoice = self.env['account.invoice'].search(
            [('move_name', '=', self.invoice_name)])

        self.assertTrue(invoice)

    def test_invoice_line_exit(self):
        invoice_line = self.env['account.invoice.line'].search(
            [('name', '=', self.invoice_line_name)])

        self.assertTrue(invoice_line)

    def test_invoice_state_is_paid(self):
        invoice = self.env['account.invoice'].search(
            [('move_name', '=', self.invoice_name)])

        self.assertEqual(invoice.state, 'paid')

    def test_payment_order_exit(self):
        payment_order = self.env['account.payment.order'].search(
            [('name', '=', self.order_name)])

        self.assertTrue(payment_order)

    def test_payment_order_state_id_uploaded(self):
        payment_order = self.env['account.payment.order'].search(
            [('name', '=', self.order_name)])

        self.assertEqual(payment_order.state, 'uploaded')

    def test_account_move_exist(self):
        payment_order = self.env['account.payment.order'].search(
            [('name', '=', self.order_name)])
        account_move = self.env['account.move'].search(
            [('payment_order_id', '=', payment_order.id)])

        self.assertTrue(account_move)

    def test_payment_line_exist(self):
        payment_line = self.env['bank.payment.line'].search(
            [('name', '=', self.payment_line_name)])

        # Check if there is a payment line
        self.assertTrue(payment_line)

    def test_account_move_deleted_after_import(self):
        self.import_file_pain002()

        payment_order = self.env['account.payment.order'].search(
            [('name', '=', self.order_name)])
        account_move = self.env['account.move'].search(
            [('payment_order_id', '=', payment_order.id)])

        self.assertFalse(account_move)

    def test_payment_line_deleted_after_import(self):
        self.import_file_pain002()
        payment_line = self.env['bank.payment.line'].search(
            [('name', '=', self.payment_line_name)])

        # Check if there is a payment line
        self.assertFalse(payment_line)
