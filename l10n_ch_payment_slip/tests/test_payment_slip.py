# -*- coding: utf-8 -*-
# © 2014-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
import re

import openerp.tests.common as test_common
from openerp.report import render_report


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
                'acc_number': 'R 12312123',
                'bvr_adherent_num': '1234567',
                'print_bank': True,
                'print_account': True,
                'print_partner': True,
            }
        )
        return bank_account

    def make_invoice(self):
        if not hasattr(self, 'bank_account'):
            self.bank_account = self.make_bank()
        account_model = self.env['account.account']
        account_debtor = account_model.search([('code', '=', '1100')])
        account_sale = account_model.search([('code', '=', '3200')])

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
