# -*- coding: utf-8 -*-
# © 2015 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests import common
from odoo import exceptions


class TestCreateInvoice(common.TransactionCase):

    def test_emit_invoice_with_bvr_reference(self):
        self.inv_values.update({
            'partner_id': self.partner.id,
            'type': 'out_invoice'
        })
        invoice = self.env['account.invoice'].new(self.inv_values)
        invoice._onchange_partner_id()
        self.assertEqual(invoice.partner_bank_id, self.bank_acc)
        self.assertNotEqual(invoice.reference_type, 'bvr')

        invoice.reference = '132000000000000000000000014'

        invoice.onchange_reference()

        self.assertEqual(invoice.reference_type, 'bvr')

    def test_emit_invoice_with_bvr_reference_15_pos(self):
        self.inv_values.update({
            'partner_id': self.partner.id,
            'type': 'out_invoice'
        })
        invoice = self.env['account.invoice'].new(self.inv_values)
        invoice._onchange_partner_id()
        self.assertEqual(invoice.partner_bank_id, self.bank_acc)
        self.assertNotEqual(invoice.reference_type, 'bvr')

        invoice.reference = '132000000000004'
        invoice.reference_type = 'bvr'  # set manually bvr reference type

        # and save
        self.env['account.invoice'].create(
            invoice._convert_to_write(invoice._cache)
        )

    def test_emit_invoice_with_non_bvr_reference(self):
        self.inv_values.update({
            'partner_id': self.partner.id,
            'type': 'out_invoice'
        })
        invoice = self.env['account.invoice'].new(self.inv_values)
        invoice._onchange_partner_id()
        self.assertEqual(invoice.partner_bank_id, self.bank_acc)
        self.assertNotEqual(invoice.reference_type, 'bvr')

        invoice.reference = 'Not a BVR ref with 27 chars'

        invoice.onchange_reference()

        self.assertNotEqual(invoice.reference_type, 'bvr')

    def test_emit_invoice_with_missing_bvr_reference(self):
        self.inv_values.update({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'account_id': 1,  # set dummy account to be replaced by onchange
        })
        invoice = self.env['account.invoice'].new(self.inv_values)

        with self.assertRaises(exceptions.ValidationError):
            invoice._onchange_partner_id()

            invoice.reference = False
            invoice.reference_type = 'bvr'  # set manually bvr reference type

            # and save
            self.env['account.invoice'].create(
                invoice._convert_to_write(invoice._cache)
            )

    def test_emit_invoice_with_bvr_reference_missing_ccp(self):
        self.inv_values.update({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'account_id': 1,  # set dummy account to be replaced by onchange
        })
        invoice = self.env['account.invoice'].new(self.inv_values)
        self.bank_acc.acc_number = 'not a CCP'

        with self.assertRaises(exceptions.ValidationError):
            invoice._onchange_partner_id()

            invoice.reference = '132000000000000000000000014'

            invoice.onchange_reference()
            invoice.reference_type = 'bvr'
            self.env['account.invoice'].create(
                invoice._convert_to_write(invoice._cache)
            )

    def setUp(self):
        super(TestCreateInvoice, self).setUp()
        self.company = self.env.ref('base.main_company')
        self.partner = self.env.ref('base.res_partner_12')
        bank = self.env['res.bank'].create({
            'name': 'BCV',
            'bic': 'BIC23423',
            'clearing': '234234',
        })
        # define company bank account
        self.bank_journal = self.env['account.journal'].create({
            'company_id': self.company.id,
            'type': 'bank',
            'code': 'BNK42',
            'bank_id': bank.id,
            'bank_acc_number': '01-1234-1',
        })
        self.bank_acc = self.bank_journal.bank_account_id
        self.payment_mode = self.env['account.payment.mode'].create({
            'name': 'Inbound Credit transfer CH',
            'company_id': self.company.id,
            'bank_account_link': 'fixed',
            'fixed_journal_id': self.bank_journal.id,
            'payment_method_id':
            self.env.ref('account.account_payment_method_manual_in').id,
        })
        self.partner.customer_payment_mode_id = self.payment_mode.id
        fields_list = [
            'company_id',
            'user_id',
            'currency_id',
            'journal_id',
        ]
        self.inv_values = self.env['account.invoice'].default_get(fields_list)
