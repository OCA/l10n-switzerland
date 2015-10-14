# -*- coding: utf-8 -*-
# © 2014-2015 Nicolas Bessi (Camptocamp SA)
# © 2015 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.tests import common
from openerp.tools import mute_logger
from openerp import exceptions


class TestBank(common.TransactionCase):

    def test_ccp_at_bank(self):
        self.bank.write({
            'ccp': '01-1234-1',
        })
        self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'bank_id': self.bank.id,
            'acc_number': 'R 12312123',
            'bvr_adherent_num': '1234567',
        })

    def test_faulty_ccp_at_bank(self):
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.bank.write({
                    'ccp': '2342342343423',
                })
                self.env['res.partner.bank'].create({
                    'partner_id': self.partner.id,
                    'bank_id': self.bank.id,
                    'acc_number': 'R 12312123',
                    'bvr_adherent_num': '1234567',
                })

    def test_non_bvr_bank(self):
        self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'bank_id': self.bank.id,
            'acc_number': 'R 12312123',
            'bvr_adherent_num': '1234567',
        })

    def test_duplicate_ccp(self):
        self.bank.write({
            'ccp': '01-1234-1',
        })
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.env['res.partner.bank'].create({
                    'partner_id': self.partner.id,
                    'bank_id': self.bank.id,
                    'acc_number': '01-1234-1',
                    'bvr_adherent_num': '1234567',
                })

    def test_constraint_adherent_number(self):
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.env['res.partner.bank'].create({
                    'partner_id': self.partner.id,
                    'acc_number': '12312123',
                    'bvr_adherent_num': 'Wrong bvr adherent number',
                })

    def test_constraint_cpp_on_partner_bank(self):
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.env['res.partner.bank'].create({
                    'partner_id': self.partner.id,
                    'acc_number': '12312123',
                    'bvr_adherent_num': 'Wrong bvr adherent number',
                    'ccp': 'Not a CCP',
                })

    def test_get_account_number(self):
        bank_account = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'bank_id': self.bank.id,
            'acc_number': 'R 12312123',
            'bvr_adherent_num': '1234567',
        })
        acc_num = bank_account.get_account_number()
        self.assertEqual(acc_num, bank_account.acc_number)
        self.bank.write({
            'ccp': '01-1234-1',
        })
        acc_num = bank_account.get_account_number()
        self.assertEqual(acc_num, bank_account.ccp)

    def test_onchange_bank(self):
        self.bank.write({
            'ccp': '01-1234-1',
        })
        bank_account = self.env['res.partner.bank'].new({
            'partner_id': self.partner.id,
            'bank_id': self.bank.id,
            'acc_number': None,
            'bvr_adherent_num': '1234567',
        })
        bank_account.onchange_bank()
        self.assertEqual(bank_account.acc_number, 'Bank/CCP 01-1234-1')

    def test_name_search(self):
        result = self.env['res.bank'].name_search('BIC234234')
        self.bank.code = 'CODE123'
        self.assertEqual(result and result[0][0], self.bank.id)
        result = self.env['res.bank'].name_search('CODE123')
        self.assertEqual(result and result[0][0], self.bank.id)
        self.bank.street = 'Route de Neuchâtel'
        self.bank.city = 'Lausanne'
        result = self.env['res.bank'].name_search('Route de Neuchâtel')
        self.assertEqual(result and result[0][0], self.bank.id)
        result = self.env['res.bank'].name_search('Lausanne')
        self.assertEqual(result and result[0][0], self.bank.id)

    def setUp(self):
        super(TestBank, self).setUp()
        self.partner = self.env.ref('base.main_partner')
        self.bank = self.env['res.bank'].create({
            'name': 'BCV',
            'bic': 'BIC234234',
            'clearing': 'CLEAR234234',
        })
