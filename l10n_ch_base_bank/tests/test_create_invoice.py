# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import common
from odoo import exceptions
from odoo.tests.common import Form


class TestCreateInvoice(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref('base.main_company')
        cls.partner = cls.env.ref('base.res_partner_12')
        bank = cls.env['res.bank'].create({
            'name': 'BCV',
            'bic': 'BBRUBEBB',
            'clearing': '234234',
        })
        # define company bank account
        cls.bank_journal = cls.env['account.journal'].create({
            'company_id': cls.company.id,
            'type': 'bank',
            'code': 'BNK42',
            'bank_id': bank.id,
            'bank_acc_number': '01-1234-1',
        })
        cls.bank_acc = cls.bank_journal.bank_account_id
        cls.payment_mode = cls.env['account.payment.mode'].create({
            'name': 'Inbound Credit transfer CH',
            'company_id': cls.company.id,
            'bank_account_link': 'fixed',
            'fixed_journal_id': cls.bank_journal.id,
            'show_bank_account_from_journal': True,
            'payment_method_id':
                cls.env.ref('account.account_payment_method_manual_in').id,
        })
        cls.partner.customer_payment_mode_id = cls.payment_mode.id
        fields_list = [
            'company_id',
            'user_id',
            'currency_id',
            'journal_id',
        ]
        cls.inv_values = cls.env['account.invoice'].default_get(fields_list)

    def new_form(self):
        inv = Form(
            self.env['account.invoice'],
            view='account.invoice_form'
        )
        inv.partner_id = self.partner
        inv.journal_id = self.bank_journal
        return inv

    def test_emit_invoice_with_isr_reference(self):
        inv_form = self.new_form()
        invoice = inv_form.save()
        self.assertEqual(invoice.partner_banks_to_show(), self.bank_acc)
        self.assertNotEqual(invoice.reference_type, 'isr')
        inv_form.reference_type = 'isr'
        invoice.reference = '132000000000000000000000014'
        inv_form.save()
        self.assertEqual(invoice.reference_type, 'isr')

    def test_emit_invoice_with_isr_reference_15_pos(self):
        inv_form = self.new_form()
        invoice = inv_form.save()

        self.assertEqual(invoice.partner_banks_to_show(), self.bank_acc)
        self.assertNotEqual(invoice.reference_type, 'isr')

        invoice.reference = '132000000000004'
        # set manually ISR reference type
        invoice.write({'reference_type': 'isr'})

        # and save
        inv_form.save()

    def test_emit_invoice_with_non_isr_reference(self):
        inv_form = self.new_form()
        invoice = inv_form.save()

        self.assertEqual(invoice.partner_banks_to_show(), self.bank_acc)
        self.assertNotEqual(invoice.reference_type, 'isr')

        invoice.reference = 'Not a ISR ref with 27 chars'
        self.assertNotEqual(invoice.reference_type, 'isr')

    def test_emit_invoice_with_missing_isr_reference(self):
        inv_form = self.new_form()
        # set dummy account to be replaced by onchange
        inv_form.account_id = self.env['account.account'].browse(1)
        inv_form.save()

        with self.assertRaises(exceptions.ValidationError):
            inv_form.reference = False
            inv_form.reference_type = 'isr'  # set manually ISR reference type
            # and save
            inv_form.save()

    def test_emit_invoice_with_isr_reference_missing_ccp(self):
        inv_form = self.new_form()
        inv_form.type = 'out_invoice'
        # set dummy account to be replaced by onchange
        inv_form.account_id = self.env['account.account'].browse(1)
        inv_form.save()

        self.bank_acc.acc_number = 'not a CCP'

        with self.assertRaises(exceptions.ValidationError):
            inv_form.reference = '132000000000000000000000014'
            inv_form.reference_type = 'isr'
            inv_form.save()
