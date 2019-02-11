# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.account_test_classes\
    import AccountingTestCase
from odoo.tools import float_compare
import time
from lxml import etree
import base64

ch_iban = 'CH15 3881 5158 3845 3843 7'


class TestSCTCH(AccountingTestCase):

    def setUp(self):
        super().setUp()
        Account = self.env['account.account']
        Journal = self.env['account.journal']
        PaymentMode = self.env['account.payment.mode']

        self.payment_order_model = self.env['account.payment.order']
        self.payment_line_model = self.env['account.payment.line']
        self.bank_line_model = self.env['bank.payment.line']
        self.partner_bank_model = self.env['res.partner.bank']
        self.attachment_model = self.env['ir.attachment']
        self.invoice_model = self.env['account.invoice']
        self.invoice_line_model = self.env['account.invoice.line']

        self.main_company = self.env.ref('base.main_company')
        self.partner_agrolait = self.env.ref('base.res_partner_2')

        self.account_expense = Account.search([(
            'user_type_id',
            '=',
            self.env.ref('account.data_account_type_expenses').id)], limit=1)
        self.account_payable = Account.search([(
            'user_type_id',
            '=',
            self.env.ref('account.data_account_type_payable').id)], limit=1)
        # Create a swiss bank
        ch_bank1 = self.env['res.bank'].create({
            'name': 'Alternative Bank Schweiz AG',
            'bic': 'ALSWCH21XXX',
            'clearing': '38815',
            'ccp': '46-110-7',
        })
        # create a ch bank account for my company
        self.cp_partner_bank = self.partner_bank_model.create({
            'acc_number': ch_iban,
            'partner_id': self.env.ref('base.main_partner').id,
            })
        self.cp_partner_bank.onchange_acc_number_set_swiss_bank()
        # create journal
        self.bank_journal = Journal.create({
            'name': 'Company Bank journal',
            'type': 'bank',
            'code': 'BNKFB',
            'bank_account_id': self.cp_partner_bank.id,
            'bank_id': ch_bank1.id,
            })
        # create a payment mode
        pay_method_id = self.env.ref(
            'account_banking_sepa_credit_transfer.sepa_credit_transfer').id
        self.payment_mode = PaymentMode.create({
            'name': 'CH credit transfer',
            'bank_account_link': 'fixed',
            'fixed_journal_id': self.bank_journal.id,
            'payment_method_id': pay_method_id,
            })
        self.payment_mode.payment_method_id.pain_version =\
            'pain.001.001.03.ch.02'
        self.chf_currency = self.env.ref('base.CHF')
        self.eur_currency = self.env.ref('base.EUR')
        ch_bank2 = self.env['res.bank'].create({
            'name': 'Banque Cantonale Vaudoise',
            'bic': 'BCVLCH2LXXX',
            'clearing': '767',
            'ccp': '01-1234-1',
        })
        # Create a bank account with clearing 767
        self.agrolait_partner_bank = self.partner_bank_model.create({
            'acc_number': 'CH9100767000S00023455',
            'partner_id': self.partner_agrolait.id,
            'bank_id': ch_bank2.id,
            'ccp': '01-1234-1',
            })

    def test_sct_ch_payment_type1(self):
        invoice1 = self.create_invoice(
            self.partner_agrolait.id,
            self.agrolait_partner_bank.id, self.eur_currency, 42.0,
            'isr', '132000000000000000000000014')
        invoice2 = self.create_invoice(
            self.partner_agrolait.id,
            self.agrolait_partner_bank.id, self.eur_currency, 12.0,
            'isr', '132000000000004')
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
        self.assertEquals(agrolait_pay_line1.currency_id, self.eur_currency)
        self.assertEquals(
            agrolait_pay_line1.partner_bank_id, invoice1.partner_bank_id)
        self.assertEquals(float_compare(
            agrolait_pay_line1.amount_currency, 42, precision_digits=accpre),
            0)
        self.assertEquals(agrolait_pay_line1.communication_type, 'isr')
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
            self.assertEquals(bank_line.currency_id, self.eur_currency)
            self.assertEquals(bank_line.communication_type, 'isr')
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
        xml_file = base64.b64decode(attachment.datas)
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
        local_instrument_xpath = xml_root.xpath(
            '//p:PmtInf/p:PmtTpInf/p:LclInstrm/p:Prtry', namespaces=namespaces)
        self.assertEquals(local_instrument_xpath[0].text, 'CH01')

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

    def test_sct_ch_payment_type3(self):
        invoice1 = self.create_invoice(
            self.partner_agrolait.id,
            self.agrolait_partner_bank.id, self.eur_currency, 4042.0,
            'none', 'Inv1242')
        invoice2 = self.create_invoice(
            self.partner_agrolait.id,
            self.agrolait_partner_bank.id, self.eur_currency, 1012.55,
            'none', 'Inv1248')
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
        self.assertEquals(agrolait_pay_line1.currency_id, self.eur_currency)
        self.assertEquals(
            agrolait_pay_line1.partner_bank_id, invoice1.partner_bank_id)
        self.assertEquals(float_compare(
            agrolait_pay_line1.amount_currency, 4042.0,
            precision_digits=accpre), 0)
        self.assertEquals(agrolait_pay_line1.communication_type, 'normal')
        self.assertEquals(
            agrolait_pay_line1.communication, 'Inv1242')
        self.payment_order.draft2open()
        self.assertEquals(self.payment_order.state, 'open')
        self.assertEquals(self.payment_order.sepa, False)
        bank_lines = self.bank_line_model.search([
            ('partner_id', '=', self.partner_agrolait.id)])
        self.assertEquals(len(bank_lines), 1)
        bank_line = bank_lines[0]
        self.assertEquals(bank_line.currency_id, self.eur_currency)
        self.assertEquals(bank_line.communication_type, 'normal')
        self.assertEquals(bank_line.communication, 'Inv1242-Inv1248')
        self.assertEquals(
            bank_line.partner_bank_id, invoice1.partner_bank_id)

        action = self.payment_order.open2generated()
        self.assertEquals(self.payment_order.state, 'generated')
        self.assertEquals(action['res_model'], 'ir.attachment')
        attachment = self.attachment_model.browse(action['res_id'])
        self.assertEquals(attachment.datas_fname[-4:], '.xml')
        xml_file = base64.b64decode(attachment.datas)
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
        local_instrument_xpath = xml_root.xpath(
            '//p:PmtInf/p:PmtTpInf/p:LclInstrm/p:Prtry', namespaces=namespaces)
        self.assertEquals(len(local_instrument_xpath), 0)

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

    def create_invoice(
            self, partner_id, partner_bank_id, currency, price_unit,
            ref_type, ref, inv_type='in_invoice'):
        invoice = self.invoice_model.create({
            'partner_id': partner_id,
            'reference_type': ref_type,
            'reference': ref,
            'currency_id': currency.id,
            'name': 'test',
            'account_id': self.account_payable.id,
            'type': inv_type,
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
        invoice.action_invoice_open()
        return invoice
