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
import openerp.tests.common as test_common
from openerp.tools import mute_logger
from openerp import exceptions


class TestBank(test_common.TransactionCase):

    def test_ccp_at_bank(self):
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        self.bank = self.env['res.bank'].create(
            {
                'name': 'BCV',
                'ccp': '01-1234-1',
                'bic': '23423456',
                'clearing': '234234',
            }
        )
        self.bank_account = self.env['res.partner.bank'].create(
            {
                'partner_id': partner.id,
                'owner_name': partner.name,
                'street':  partner.street,
                'city': partner.city,
                'zip':  partner.zip,
                'state': 'bvr',
                'bank': self.bank.id,
                'bank_name': self.bank.name,
                'bank_bic': self.bank.bic,
                'acc_number': 'R 12312123',
                'bvr_adherent_num': '1234567',
            }
        )

    def test_faulty_ccp_at_bank(self):
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.bank = self.env['res.bank'].create(
                    {
                        'name': 'BCV',
                        'ccp': '2342342343423',
                        'bic': '23423456',
                        'clearing': '234234',
                    }
                )

                self.bank_account = self.env['res.partner.bank'].create(
                    {
                        'partner_id': partner.id,
                        'owner_name': partner.name,
                        'street':  partner.street,
                        'city': partner.city,
                        'zip':  partner.zip,
                        'state': 'bvr',
                        'bank': self.bank.id,
                        'bank_name': self.bank.name,
                        'bank_bic': self.bank.bic,
                        'acc_number': 'R 12312123',
                        'bvr_adherent_num': '1234567',

                    }
                )

    def test_non_bvr_bank(self):
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        self.bank = self.env['res.bank'].create(
            {
                'name': 'BCV',
                'bic': '23423456',
                'clearing': '234234',
            }
        )
        self.bank_account = self.env['res.partner.bank'].create(
            {
                'partner_id': partner.id,
                'owner_name': partner.name,
                'street':  partner.street,
                'city': partner.city,
                'zip':  partner.zip,
                'state': 'bank',
                'bank': self.bank.id,
                'bank_name': self.bank.name,
                'bank_bic': self.bank.bic,
                'acc_number': 'R 12312123',
                'bvr_adherent_num': '1234567',
            }
        )

    # Commented du to issue odoo#3422
    # def test_duplicate_ccp(self):
    #     company = self.env.ref('base.main_company')
    #     self.assertTrue(company)
    #     partner = self.env.ref('base.main_partner')
    #     self.assertTrue(partner)
    #     self.bank = self.env['res.bank'].create(
    #         {
    #             'name': 'BCV',
    #             'bic': '234234',
    #             'clearing': '234234',
    #             'ccp': '01-1234-1',
    #             'bvr_adherent_num': '1234567',

    #         }
    #     )
    #     with self.assertRaises(exceptions.ValidationError):
    #         with mute_logger():
    #             self.bank_account = self.env['res.partner.bank'].create(
    #                 {
    #                     'partner_id': partner.id,
    #                     'owner_name': partner.name,
    #                     'street':  partner.street,
    #                     'city': partner.city,
    #                     'zip':  partner.zip,
    #                     'state': 'bvr',
    #                     'bank': self.bank.id,
    #                     'bank_name': self.bank.name,
    #                     'bank_bic': self.bank.bic,
    #                     'acc_number': '01-1234-1',
    #                     'bvr_adherent_num': '1234567',
    #                 }
    #             )
