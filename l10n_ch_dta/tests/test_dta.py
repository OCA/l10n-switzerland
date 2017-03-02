# -*- coding: utf-8 -*-
# Copyright 2016 Braintec AG - Kumar Aberer <kumar.aberer@braintec-group.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo import tools
from odoo.tools import float_compare
from odoo.modules.module import get_resource_path

from odoo.addons.account.tests.account_test_classes \
    import AccountingTestCase


class TestDTA(AccountingTestCase):

    def _load(self, module, *args):
        tools.convert_file(
            self.cr, 'account_asset',
            get_resource_path(module, *args),
            {}, 'init', False, 'test', self.registry._assertion_report)

    def test_dta(self):
        self._load('account', 'test', 'account_minimal_test.xml')
        self.company = self.env['res.company']
        self.account_model = self.env['account.account']
        self.move_model = self.env['account.move']
        self.journal_model = self.env['account.journal']
        self.payment_order_model = self.env['account.payment.order']
        self.payment_line_model = self.env['account.payment.line']
        self.bank_line_model = self.env['bank.payment.line']
        self.partner_bank_model = self.env['res.partner.bank']
        self.attachment_model = self.env['ir.attachment']
        self.invoice_model = self.env['account.invoice']
        self.invoice_line_model = self.env['account.invoice.line']
        company = self.env.ref('base.main_company')
        self.partner_agrolait = self.env.ref('base.res_partner_2')
        self.partner_c2c = self.env.ref('base.res_partner_12')
        self.account_expense = self.account_model.search([(
            'user_type_id',
            '=',
            self.env.ref('account.data_account_type_expenses').id)], limit=1)
        self.account_payable = self.account_model.search([(
            'user_type_id',
            '=',
            self.env.ref('account.data_account_type_payable').id)], limit=1)
        # update clearing number
        self.env.ref('account_payment_mode.bank_la_banque_postale').write(
            {'clearing': 'FR'})
        # create journal
        self.bank_journal = self.journal_model.create({
            'name': 'Company Bank journal',
            'type': 'bank',
            'code': 'BNKFB',
            'bank_account_id':
                self.env.ref('account_payment_mode.main_company_iban').id,
            'bank_id':
                self.env.ref('account_payment_mode.bank_la_banque_postale').id,
        })
        # update payment mode
        self.payment_mode = self.env.ref(
            'l10n_ch_dta.'
            'payment_mode_dta')

        self.payment_mode.write({
            'bank_account_link': 'fixed',
            'fixed_journal_id': self.bank_journal.id,
        })

        eur_currency_id = self.env.ref('base.EUR').id
        company.currency_id = eur_currency_id
        invoice1 = self.create_invoice(
            self.partner_agrolait.id,
            'account_payment_mode.res_partner_2_iban', 42.0, 'F1341')
        invoice2 = self.create_invoice(
            self.partner_agrolait.id,
            'account_payment_mode.res_partner_2_iban', 12.0, 'F1342')
        invoice3 = self.create_invoice(
            self.partner_agrolait.id,
            'account_payment_mode.res_partner_2_iban', 5.0, 'A1301',
            'in_refund')
        invoice4 = self.create_invoice(
            self.partner_c2c.id,
            'account_payment_mode.res_partner_12_iban', 11.0, 'I1642')
        invoice5 = self.create_invoice(
            self.partner_c2c.id,
            'account_payment_mode.res_partner_12_iban', 41.0, 'I1643')
        for inv in [invoice1, invoice2, invoice3, invoice4, invoice5]:
            action = inv.create_account_payment_line()
        self.assertEquals(action['res_model'], 'account.payment.order')
        self.payment_order = self.payment_order_model.browse(action['res_id'])
        self.assertEquals(
            self.payment_order.payment_type, 'outbound')
        self.assertEquals(
            self.payment_order.payment_mode_id, self.payment_mode)
        self.assertEquals(
            self.payment_order.journal_id, self.bank_journal)
        pay_lines = self.payment_line_model.search([
            ('partner_id', '=', self.partner_agrolait.id),
            ('order_id', '=', self.payment_order.id)])
        self.assertEquals(len(pay_lines), 3)
        agrolait_pay_line1 = pay_lines[0]
        accpre = self.env['decimal.precision'].precision_get('Account')
        self.assertEquals(agrolait_pay_line1.currency_id.id, eur_currency_id)
        self.assertEquals(
            agrolait_pay_line1.partner_bank_id, invoice1.partner_bank_id)
        self.assertEquals(float_compare(
            agrolait_pay_line1.amount_currency, 42, precision_digits=accpre),
            0)
        self.assertEquals(agrolait_pay_line1.communication_type, 'normal')
        self.assertEquals(agrolait_pay_line1.communication, 'F1341')
        self.payment_order.draft2open()
        self.assertEquals(self.payment_order.state, 'open')
        bank_lines = self.bank_line_model.search([
            ('partner_id', '=', self.partner_agrolait.id)])
        self.assertEquals(len(bank_lines), 1)
        agrolait_bank_line = bank_lines[0]
        self.assertEquals(agrolait_bank_line.currency_id.id, eur_currency_id)
        self.assertEquals(float_compare(
            agrolait_bank_line.amount_currency, 49.0, precision_digits=accpre),
            0)
        self.assertEquals(agrolait_bank_line.communication_type, 'normal')
        self.assertEquals(
            agrolait_bank_line.communication, 'F1341-F1342-A1301')
        self.assertEquals(
            agrolait_bank_line.partner_bank_id, invoice1.partner_bank_id)

        action = self.payment_order.open2generated()
        self.assertEquals(self.payment_order.state, 'generated')
        self.assertEquals(action['res_model'], 'ir.attachment')
        attachment = self.attachment_model.browse(action['res_id'])
        self.assertEquals(attachment.datas_fname[-4:], '.txt')
        dta_file = attachment.datas.decode('base64')
        self.assertEquals(dta_file[:2], '01')
        self.payment_order.generated2uploaded()
        self.assertEquals(self.payment_order.state, 'uploaded')
        for inv in [invoice1, invoice2, invoice3, invoice4, invoice5]:
            self.assertEquals(inv.state, 'paid')
        return

    def create_invoice(
            self, partner_id, partner_bank_xmlid, price_unit, reference,
            type='in_invoice'):
        invoice = self.invoice_model.create({
            'partner_id': partner_id,
            'reference_type': 'none',
            'reference': reference,
            'currency_id': self.env.ref('base.EUR').id,
            'name': 'test',
            'account_id': self.account_payable.id,
            'type': type,
            'date_invoice': time.strftime('%Y-%m-%d'),
            'payment_mode_id': self.payment_mode.id,
            'partner_bank_id': self.env.ref(partner_bank_xmlid).id,
        })
        self.invoice_line_model.create({
            'invoice_id': invoice.id,
            'price_unit': price_unit,
            'quantity': 1,
            'name': 'Great service',
            'account_id': self.account_expense.id,
        })
        invoice.invoice_validate()
        invoice.action_move_create()
        return invoice
