# -*- coding: utf-8 -*-
# © 2014-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
import re

from openerp import tools
import openerp.tests.common as test_common
from openerp.report import render_report
from openerp.modules.module import get_module_resource


class TestPaymentSlip(test_common.TransactionCase):
    _compile_get_ref = re.compile(r'[^0-9]')

    def make_bank(self):
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        bank = self.env['res.bank'].create(
            {
                'name': 'BCV',
                'ccp': '01-1234-1',
                'bic': '23452345',
                'clearing': '234234',
            }
        )
        bank_account = self.env['res.partner.bank'].create(
            {
                'partner_id': partner.id,
                'bank_id': bank.id,
                'bank_bic': bank.bic,
                'acc_number': '01-1234-1',
                'bvr_adherent_num': '1234567',
                'print_bank': True,
                'print_account': True,
                'print_partner': True,
            }
        )
        bank_account.onchange_acc_number_set_swiss_bank()
        self.assertEqual(bank_account.ccp, '01-1234-1')
        return bank_account

    def make_invoice(self):
        if not hasattr(self, 'bank_account'):
            self.bank_account = self.make_bank()
        account_model = self.env['account.account']
        account_debtor = account_model.search([('code', '=', 'X1012')])
        account_sale = account_model.search([('code', '=', 'X2020')])

        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'reference_type': 'none',
            'name': 'A customer invoice',
            'account_id': account_debtor.id,
            'type': 'out_invoice',
            'partner_bank_id': self.bank_account.id
        })

        self.env['account.invoice.line'].create({
            'account_id': account_sale.id,
            'product_id': False,
            'quantity': 1,
            'price_unit': 862.50,
            'invoice_id': invoice.id,
            'name': 'product that cost 862.50 all tax included',
        })
        invoice.signal_workflow('invoice_open')
        # waiting for the cache to refresh
        attempt = 0
        while not invoice.move_id:
            invoice.refresh()
            time.sleep(0.1)
            attempt += 1
            if attempt > 20:
                break
        return invoice

    def test_invoice_confirmation(self):
        """Test that confirming an invoice generate slips correctly"""
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        for line in invoice.move_id.line_ids:
            if line.account_id.user_type_id.type in ('payable', 'receivable'):
                self.assertTrue(line.transaction_ref)
            else:
                self.assertFalse(line.transaction_ref)
        for line in invoice.move_id.line_ids:
            slip = self.env['l10n_ch.payment_slip'].search(
                [('move_line_id', '=', line.id)]
            )
            if line.account_id.user_type_id.type in ('payable', 'receivable'):
                self.assertTrue(slip)
                self.assertEqual(slip.amount_total, 862.50)
                self.assertEqual(slip.invoice_id.id, invoice.id)
            else:
                self.assertFalse(slip)

    def test_slip_validity(self):
        """Test that confirming slip are valid"""
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        for line in invoice.move_id.line_ids:
            slip = self.env['l10n_ch.payment_slip'].search(
                [('move_line_id', '=', line.id)]
            )
            if line.account_id.user_type_id.type in ('payable', 'receivable'):
                self.assertTrue(slip.reference)
                self.assertTrue(slip.scan_line)
                self.assertTrue(slip.slip_image)
                self.assertTrue(slip.a4_pdf)
                inv_num = line.invoice_id.number
                line_ident = self._compile_get_ref.sub(
                    '', "%s%s" % (inv_num, line.id)
                )
                self.assertIn(line_ident, slip.reference.replace(' ', ''))

    def test_print_report(self):
        invoice = self.make_invoice()
        data, format = render_report(
            self.env.cr,
            self.env.uid,
            [invoice.id],
            'l10n_ch_payment_slip.one_slip_per_page_from_invoice',
            {},
            context={'force_pdf': True},
        )
        self.assertTrue(data)
        self.assertEqual(format, 'pdf')

    def test_print_multi_report_merge_in_memory(self):
        # default value as in memory
        self.assertEqual(self.env.user.company_id.merge_mode, 'in_memory')
        invoice1 = self.make_invoice()
        invoice2 = self.make_invoice()
        data, format = render_report(
            self.env.cr,
            self.env.uid,
            [invoice1.id, invoice2.id],
            'l10n_ch_payment_slip.one_slip_per_page_from_invoice',
            {},
            context={'force_pdf': True},
        )
        self.assertTrue(data)
        self.assertEqual(format, 'pdf')

    def test_print_multi_report_merge_on_disk(self):
        self.env.user.company_id.merge_mode = 'on_disk'
        invoice1 = self.make_invoice()
        invoice2 = self.make_invoice()
        data, format = render_report(
            self.env.cr,
            self.env.uid,
            [invoice1.id, invoice2.id],
            'l10n_ch_payment_slip.one_slip_per_page_from_invoice',
            {},
            context={'force_pdf': True},
        )
        self.assertTrue(data)
        self.assertEqual(format, 'pdf')

    def test_address_format(self):
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        line = invoice.move_id.line_ids[0]
        slip = self.env['l10n_ch.payment_slip'].search(
            [('move_line_id', '=', line.id)]
        )
        com_partner = slip.get_comm_partner()
        address_lines = slip._get_address_lines(com_partner)
        self.assertEqual(
            address_lines,
            [u'93, Press Avenue', u'', u'73377 Le Bourget du Lac']
        )

    def test_address_format_no_country(self):
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        line = invoice.move_id.line_ids[0]
        slip = self.env['l10n_ch.payment_slip'].search(
            [('move_line_id', '=', line.id)]
        )
        com_partner = slip.get_comm_partner()
        com_partner.country_id = False
        address_lines = slip._get_address_lines(com_partner)
        self.assertEqual(
            address_lines,
            [u'93, Press Avenue', u'', u'73377 Le Bourget du Lac']
        )

    def test_address_format_special_format(self):
        """ Test special formating without street2 """

        ICP = self.env['ir.config_parameter']
        ICP.set_param(
            'bvr.address.format',
            "%(street)s\n%(zip)s %(city)s"
        )
        invoice = self.make_invoice()
        self.assertTrue(invoice.move_id)
        line = invoice.move_id.line_ids[0]
        slip = self.env['l10n_ch.payment_slip'].search(
            [('move_line_id', '=', line.id)]
        )
        com_partner = slip.get_comm_partner()
        com_partner.country_id = False
        address_lines = slip._get_address_lines(com_partner)
        self.assertEqual(
            address_lines,
            [u'93, Press Avenue', u'73377 Le Bourget du Lac']
        )

    def _load(self, module, *args):
        tools.convert_file(
            self.cr, 'account_asset',
            get_module_resource(module, *args),
            {}, 'init', False, 'test', self.registry._assertion_report)

    def setUp(self):
        super(TestPaymentSlip, self).setUp()
        self._load('account', 'test', 'account_minimal_test.xml')
