from odoo.tests import TransactionCase
from odoo.modules import get_module_resource

import time


class TestImportPain002(TransactionCase):

    def import_file_pain002(self):
        test_file_path = get_module_resource('l10n_ch_import_pain002',
                                             'test_files',
                                             'pain002p-rejected.xml')

        file_to_import = open(test_file_path, 'r')
        data = file_to_import.read()
        data = data.replace("\n", "")

        self.account_pain002.parse(data)

    def create_invoice(self):
        """ Generates a test invoice """
        account_receivable = self.env['account.account'].search([
            ('user_type_id', '=', self.env.ref(
                'account.data_account_type_receivable').id)
        ], limit=1)
        currency = self.env.ref('base.CHF')
        partner_agrolait = self.env.ref("base.res_partner_2")
        product = self.env.ref("product.product_product_4")
        account_revenue = self.env['account.account'].search([
            ('user_type_id', '=', self.env.ref(
                'account.data_account_type_revenue').id)
        ], limit=1)

        invoice = self.env['account.invoice'].create({
            'partner_id': partner_agrolait.id,
            'reference_type': 'none',
            'currency_id': currency.id,
            'name': 'invoice to client',
            'account_id': account_receivable.id,
            'type': 'out_invoice',
            'date_invoice': time.strftime('%Y') + '-12-22',
        })

        self.env['account.invoice.line'].create({
            'product_id': product.id,
            'quantity': 1,
            'price_unit': 42,
            'invoice_id': invoice.id,
            'name': 'something',
            'account_id': account_revenue.id,
        })

        # invoice.action_invoice_open()

        return invoice

    def create_journal(self, name, company):
        # Create a cash account
        # Create a journal for cash account
        journal = self.env['account.journal'].create({
            'name': name,
            'code': name,
            'type': 'bank',
            'company_id': company.id,
            'update_posted': True
        })
        return journal

    def setUp(self):
        super().setUp()

        self.order_name = '2017/1013'
        self.journal_name = '2017/1013'
        self.payment_line_name = 'Ltest'
        self.company = self.env.ref('base.main_company')

        self.account_pain002 = self.env['account.pain002.parser']

        self.invoice = self.create_invoice()

        # Validate the invoice
        self.invoice.action_invoice_open()
        self.invoice.payment_mode_id.payment_order_ok = True

        # Create a payment order
        action = self.invoice.create_account_payment_line()
        payment_order_id = action['res_id']

        self.payment_order = self.env['account.payment.order'].search(
            [('id', '=', payment_order_id)])

        partner_bank = self.create_journal(self.journal_name, self.company)

        bank = self.env['account.journal'].search([('name', '=', 'Bank')])

        self.payment_order.name = self.order_name
        bank.update_posted = True

        self.payment_order.journal_id = partner_bank.id
        # Confirm payment order
        self.payment_order.draft2open()
        # Generate payment file
        self.payment_order.open2generated()
        # File successfully uploaded
        self.payment_order.generated2uploaded()

        # Adapt payment line to mach with the pain002 file
        payment_line = self.env['bank.payment.line'].search(
            [('order_id', '=', self.payment_order.id)])

        payment_line.name = self.payment_line_name

        # self.env.cr.commit()

    def test_invoice_state_is_paid(self):
        self.assertEqual(self.invoice.state, 'paid')

    def test_payment_order_state_id_uploaded(self):
        self.assertEqual(self.payment_order.state, 'uploaded')

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
