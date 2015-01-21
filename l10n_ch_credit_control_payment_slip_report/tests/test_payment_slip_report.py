# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
import openerp.tests.common as test_common


class TestPaymentSlipReport(test_common.TransactionCase):

    def make_bank(self):
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        bank = self.env['res.bank'].create(
            {
                'name': 'BCV',
                'ccp': '01-1234-1',
                'bic': '234234',
                'clearing': '234234',
            }
        )
        bank_account = self.env['res.partner.bank'].create(
            {
                'partner_id': partner.id,
                'owner_name': partner.name,
                'street':  partner.street,
                'city': partner.city,
                'zip':  partner.zip,
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
                'account_id': self.env.ref('account.a_recv').id,
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
            }
        )
        invoice.signal_workflow('invoice_open')
        attempt = 0
        while not invoice.move_id:
            invoice.refresh()
            time.sleep(0.1)
            attempt += 1
            if attempt > 20:
                break
        self.assertTrue(invoice.move_id)
        self.assertEqual(invoice.amount_total, 862.50)
        return invoice

    def test_amount_with_fees(self):
        """Test that dunning fees are included in payment slip's amount"""
        invoice = self.make_invoice()
        move_line = self.env['account.move.line'].search(
            [('invoice', '=', invoice.id),
             ('account_id.type', 'in', ('payable', 'receivable'))],
        )
        self.assertTrue(len(move_line), 1)

        lvl = self.env.ref('account_credit_control.3_time_1')
        credit_line = self.env['credit.control.line'].create(
            {'move_line_id': move_line.id,
             'date_due': '2000-01-01',
             'partner_id': self.env.ref('base.res_partner_12').id,
             'channel': 'email',
             'date':  '2000-01-01',
             'balance_due': 100.00,
             'amount_due': 100.00,
             'policy_level_id': lvl.id,
             'state': 'to_be_sent'}
        )
        slip_obj = self.env['l10n_ch.payment_slip'].with_context(
            __slip_credit_control_line_id=credit_line.id
        )
        slip = slip_obj.search([('move_line_id', '=', move_line.id)])
        self.assertEqual(slip.amount_total, 862.50)
        credit_line.dunning_fees_amount = 30000
        self.assertEqual(slip.amount_total, 30862.50)

    def test_printing(self):
        """Test that we can print the report"""
        invoice = self.make_invoice()
        move_line = self.env['account.move.line'].search(
            [('invoice', '=', invoice.id),
             ('account_id.type', 'in', ('payable', 'receivable'))],
        )
        self.assertTrue(len(move_line), 1)

        lvl = self.env.ref('account_credit_control.3_time_1')
        credit_line = self.env['credit.control.line'].create(
            {'move_line_id': move_line.id,
             'date_due': '2000-01-01',
             'partner_id': self.env.ref('base.res_partner_12').id,
             'channel': 'email',
             'date':  '2000-01-01',
             'balance_due': 100.00,
             'amount_due': 100.00,
             'policy_level_id': lvl.id,
             'state': 'to_be_sent'}
        )
        report_name = 'slip_from_credit_control'
        report_obj = self.env['report'].with_context(
            active_ids=credit_line.ids)
        return report_obj.get_action(credit_line, report_name)
