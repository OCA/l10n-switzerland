# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.account.tests.account_test_classes\
    import AccountingTestCase
from openerp.tools import float_compare
import time
from lxml import etree


class TestSCT_CH(AccountingTestCase):

    def test_sct_ch(self):
        self.company = self.env['res.company']
        self.account_model = self.env['account.account']
        self.move_model = self.env['account.move']
        self.journal_model = self.env['account.journal']
        self.payment_mode_model = self.env['account.payment.mode']
        self.payment_order_model = self.env['account.payment.order']
        self.payment_line_model = self.env['account.payment.line']
        self.bank_line_model = self.env['bank.payment.line']
        self.partner_bank_model = self.env['res.partner.bank']
        self.bank_model = self.env['res.bank']
        self.attachment_model = self.env['ir.attachment']
        self.invoice_model = self.env['account.invoice']
        self.invoice_line_model = self.env['account.invoice.line']
        company = self.env.ref('base.main_company')
        self.partner_agrolait = self.env.ref('base.res_partner_2')
        self.account_expense = self.account_model.search([(
            'user_type_id',
            '=',
            self.env.ref('account.data_account_type_expenses').id)], limit=1)
        self.account_payable = self.account_model.search([(
            'user_type_id',
            '=',
            self.env.ref('account.data_account_type_payable').id)], limit=1)
        # Create a swiss bank
        ch_bank = self.bank_model.create({
            'name': 'Big swiss bank',
            'bic': 'DRESDEFF300',
            'ccp': '01-1234-1',
            })
        # create a ch bank account for my company
        my_ch_partner_bank = self.partner_bank_model.create({
            'acc_number': 'CH0909000000100080607',
            'partner_id': self.env.ref('base.main_partner').id,
            'bank_id': ch_bank.id,
            })
        # create journal
        self.bank_journal = self.journal_model.create({
            'name': 'Company Bank journal',
            'type': 'bank',
            'code': 'BNKFB',
            'bank_account_id': my_ch_partner_bank.id,
            'bank_id': ch_bank.id,
            })
        # create a payment mode
        pay_method_id = self.env.ref(
            'account_banking_sepa_credit_transfer.sepa_credit_transfer').id
        self.payment_mode = self.payment_mode_model.create({
            'name': 'CH credit transfer',
            'bank_account_link': 'fixed',
            'fixed_journal_id': self.bank_journal.id,
            'payment_method_id': pay_method_id,
            })
        self.payment_mode.payment_method_id.pain_version =\
            'pain.001.001.03.ch.02'
        chf_currency_id = self.env.ref('base.CHF').id
        company.currency_id = chf_currency_id
        # Create a bank account
        ch_partner_bank = self.partner_bank_model.create({
            'acc_number': 'CH9100767000S00023455',
            'partner_id': self.partner_agrolait.id,
            'bank_id': ch_bank.id,
            })
        invoice1 = self.create_bvr_invoice(
            self.partner_agrolait.id,
            ch_partner_bank.id, 42.0, '132000000000000000000000014')
        invoice2 = self.create_bvr_invoice(
            self.partner_agrolait.id,
            ch_partner_bank.id, 12.0, '132000000000004')
        for inv in [invoice1, invoice2]:
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
        self.assertEquals(len(pay_lines), 2)
        agrolait_pay_line1 = pay_lines[0]
        accpre = self.env['decimal.precision'].precision_get('Account')
        self.assertEquals(agrolait_pay_line1.currency_id.id, chf_currency_id)
        self.assertEquals(
            agrolait_pay_line1.partner_bank_id, invoice1.partner_bank_id)
        self.assertEquals(float_compare(
            agrolait_pay_line1.amount_currency, 42, precision_digits=accpre),
            0)
        self.assertEquals(agrolait_pay_line1.communication_type, 'bvr')
        self.assertEquals(
            agrolait_pay_line1.communication,
            '132000000000000000000000014')
        self.payment_order.draft2open()
        self.assertEquals(self.payment_order.state, 'open')
        self.assertEquals(self.payment_order.sepa, False)
        bank_lines = self.bank_line_model.search([
            ('partner_id', '=', self.partner_agrolait.id)])
        self.assertEquals(len(bank_lines), 2)
        for bank_line in bank_lines:
            self.assertEquals(bank_line.currency_id.id, chf_currency_id)
            self.assertEquals(bank_line.communication_type, 'bvr')
            self.assertEquals(
                bank_line.communication in [
                    '132000000000000000000000014',
                    '132000000000004'], True)
            self.assertEquals(
                bank_line.partner_bank_id, invoice1.partner_bank_id)

        action = self.payment_order.open2generated()
        self.assertEquals(self.payment_order.state, 'generated')
        self.assertEquals(action['res_model'], 'ir.attachment')
        attachment = self.attachment_model.browse(action['res_id'])
        self.assertEquals(attachment.datas_fname[-4:], '.xml')
        xml_file = attachment.datas.decode('base64')
        xml_root = etree.fromstring(xml_file)
        # print "xml_file=", etree.tostring(xml_root, pretty_print=True)
        namespaces = xml_root.nsmap
        namespaces['p'] = xml_root.nsmap[None]
        namespaces.pop(None)
        pay_method_xpath = xml_root.xpath(
            '//p:PmtInf/p:PmtMtd', namespaces=namespaces)
        self.assertEquals(
            namespaces['p'],
            'http://www.six-interbank-clearing.com/de/'
            'pain.001.001.03.ch.02.xsd')
        self.assertEquals(pay_method_xpath[0].text, 'TRF')
        sepa_xpath = xml_root.xpath(
            '//p:PmtInf/p:PmtTpInf/p:SvcLvl/p:Cd', namespaces=namespaces)
        self.assertEquals(len(sepa_xpath), 0)
        debtor_acc_xpath = xml_root.xpath(
            '//p:PmtInf/p:DbtrAcct/p:Id/p:IBAN', namespaces=namespaces)
        self.assertEquals(
            debtor_acc_xpath[0].text,
            self.payment_order.company_partner_bank_id.sanitized_acc_number)
        self.payment_order.generated2uploaded()
        self.assertEquals(self.payment_order.state, 'uploaded')
        for inv in [invoice1, invoice2]:
            self.assertEquals(inv.state, 'paid')
        return

    def create_bvr_invoice(
            self, partner_id, partner_bank_id, price_unit, reference,
            type='in_invoice'):
        invoice = self.invoice_model.create({
            'partner_id': partner_id,
            'reference_type': 'bvr',
            'reference': reference,
            'currency_id': self.env.ref('base.CHF').id,
            'name': 'test',
            'account_id': self.account_payable.id,
            'type': type,
            'date_invoice': time.strftime('%Y-%m-%d'),
            'payment_mode_id': self.payment_mode.id,
            'partner_bank_id': partner_bank_id,
            })
        self.invoice_line_model.create({
            'invoice_id': invoice.id,
            'price_unit': price_unit,
            'quantity': 1,
            'name': 'Great service',
            'account_id': self.account_expense.id,
            })
        invoice.signal_workflow('invoice_open')
        return invoice
