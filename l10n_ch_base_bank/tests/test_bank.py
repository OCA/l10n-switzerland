# Copyright 2014-2015 Nicolas Bessi (Camptocamp SA)
# Copyright 2015-2017 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import common
from odoo.tools import mute_logger
from odoo import exceptions

ch_iban = 'CH15 3881 5158 3845 3843 7'
ch_post_iban = 'CH09 0900 0000 1000 8060 7'
fr_iban = 'FR8387234133870990794002530'


class TestBank(common.TransactionCase):

    def setUp(self):
        super(TestBank, self).setUp()
        self.partner = self.env.ref('base.res_partner_12')
        self.bank = self.env['res.bank'].create({
            'name': 'Alternative Bank Schweiz AG',
            'bic': 'ALSWCH21XXX',
            'clearing': '38815',
            'ccp': '46-110-7',
        })
        self.post_bank = self.env['res.bank'].search(
            [('bic', '=', 'POFICHBEXXX')])
        if not self.post_bank:
            self.post_bank = self.env['res.bank'].create({
                'name': 'PostFinance AG',
                'bic': 'POFICHBEXXX',
                'clearing': '9000',
                'ccp': '10-8060-7',
            })

    def test_bank_iban(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': ch_iban.replace(' ', ''),
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertEqual(bank_acc.bank_id, self.bank)
        self.assertEqual(bank_acc.acc_number, ch_iban.replace(' ', ''))
        self.assertEqual(bank_acc.ccp, '46-110-7')
        self.assertEqual(bank_acc.acc_type, 'iban')

    def test_bank_iban_with_spaces(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': ch_iban,
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertEqual(bank_acc.bank_id, self.bank)
        self.assertEqual(bank_acc.acc_number, ch_iban)
        self.assertEqual(bank_acc.ccp, '46-110-7')
        self.assertEqual(bank_acc.acc_type, 'iban')

    def test_bank_iban_lower_case(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': ch_iban.lower(),
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertEqual(bank_acc.bank_id, self.bank)
        self.assertEqual(bank_acc.acc_number, ch_iban.lower())
        self.assertEqual(bank_acc.ccp, '46-110-7')
        self.assertEqual(bank_acc.acc_type, 'iban')

    def test_bank_iban_foreign(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': fr_iban,
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertFalse(bank_acc.bank_id)
        self.assertEqual(bank_acc.acc_number, fr_iban)
        self.assertFalse(bank_acc.ccp)
        self.assertEqual(bank_acc.acc_type, 'iban')

    def test_bank_ccp(self):
        # test UI onchange methods
        bank_acc = self.env['res.partner.bank'].new({
            'partner_id': self.partner.id,
            'acc_number': '46-110-7',
        })

        bank_acc.onchange_acc_number_set_swiss_bank()
        # ccp also changed
        bank_acc.onchange_ccp_set_acc_number()

        self.assertEqual(bank_acc.bank_id, self.bank)
        self.assertEqual(bank_acc.acc_number, 'Camptocamp/CCP 46-110-7')
        self.assertEqual(bank_acc.ccp, '46-110-7')
        self.assertEqual(bank_acc.acc_type, 'bank')

    def test_bank_ccp_no_found(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': '10-8060-7',
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertEqual(bank_acc.bank_id, self.post_bank)
        # if acc_number given by user don't update it
        self.assertEqual(bank_acc.acc_number, '10-8060-7')
        self.assertEqual(bank_acc.ccp, '10-8060-7')
        self.assertEqual(bank_acc.acc_type, 'postal')

        bank_acc.bank_id = self.post_bank
        bank_acc.onchange_bank_set_acc_number()
        bank_acc.onchange_ccp_set_acc_number()

        self.assertEqual(bank_acc.bank_id, self.post_bank)
        # copied ccp to acc_number
        self.assertEqual(bank_acc.acc_number, '10-8060-7')
        self.assertEqual(bank_acc.ccp, '10-8060-7')
        self.assertEqual(bank_acc.acc_type, 'postal')

    def test_ccp(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': '10-8060-7',
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertEqual(bank_acc.bank_id, self.post_bank)
        self.assertEqual(bank_acc.acc_number, '10-8060-7')
        self.assertEqual(bank_acc.ccp, '10-8060-7')
        self.assertEqual(bank_acc.acc_type, 'postal')

    def test_iban_ccp(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': ch_post_iban.replace(' ', ''),
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertEqual(bank_acc.bank_id, self.post_bank)
        self.assertEqual(bank_acc.acc_number, ch_post_iban.replace(' ', ''))
        self.assertEqual(bank_acc.ccp, '10-8060-7')
        self.assertEqual(bank_acc.acc_type, 'iban')

    def test_iban_ccp_with_spaces(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': ch_post_iban,
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertEqual(bank_acc.bank_id, self.post_bank)
        self.assertEqual(bank_acc.acc_number, ch_post_iban)
        self.assertEqual(bank_acc.ccp, '10-8060-7')
        self.assertEqual(bank_acc.acc_type, 'iban')

    def test_other_bank(self):
        self.bank.ccp = False
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'bank_id': self.bank.id,
            'acc_number': 'R 12312123',
        })
        bank_acc.onchange_acc_number_set_swiss_bank()

        self.assertEqual(bank_acc.bank_id, self.bank)
        self.assertEqual(bank_acc.acc_number, 'R 12312123')
        self.assertEqual(bank_acc.ccp, False)
        self.assertEqual(bank_acc.acc_type, 'bank')

    def test_set_ccp(self):
        bank_acc = self.env['res.partner.bank'].new({
            'partner_id': self.partner.id,
            'acc_number': None,
            'ccp': '10-8060-7',
        })
        bank_acc.onchange_ccp_set_acc_number()

        self.assertEqual(bank_acc.acc_number, '10-8060-7')
        self.assertEqual(bank_acc.bank_id, self.post_bank)

    def test_set_ccp_bank(self):
        # we crate bank account
        # action runs in UI before creation
        with self.env.do_in_onchange():

            bank_acc = self.env['res.partner.bank'].new({
                'partner_id': self.partner.id,
                'acc_number': None,
                'bank_id': self.bank.id,
                'ccp': '10-8060-7'
            })
            bank_acc.onchange_ccp_set_acc_number()
            # in result we should get new ccp number as we have bank_id and
            # this he has ccp, new acc_number

            self.assertEqual(bank_acc.acc_number, 'Camptocamp/CCP 10-8060-7')
            self.assertEqual(bank_acc.ccp, '10-8060-7')
            self.assertEqual(bank_acc.bank_id, self.bank)

    def test_set_onchange_ccp_post(self):
        # fond bank based on ccp set acc_number
        # action runs in UI before creation
        bank_acc = self.env['res.partner.bank'].new({
            'partner_id': self.partner.id,
            'ccp': '10-8060-7'
        })
        bank_acc.onchange_ccp_set_acc_number()
        self.assertEqual(bank_acc.acc_number, '10-8060-7')
        self.assertEqual(bank_acc.ccp, '10-8060-7')
        self.assertEqual(bank_acc.bank_id, self.post_bank)

    def test_constraint_ccp(self):
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.env['res.partner.bank'].create({
                    'partner_id': self.partner.id,
                    'bank_id': self.bank.id,
                    'acc_number': 'R 12312123',
                    'ccp': '520-54025-54054',
                })

    def test_constraint_ccp_at_bank(self):
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.bank.ccp = '999999999999'

    def test_constraint_adherent_number(self):
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.env['res.partner.bank'].create({
                    'partner_id': self.partner.id,
                    'acc_number': '12312123',
                    'isr_adherent_num': 'Wrong ISR adherent number',
                })

    def test_get_account_number(self):
        """ get_account_number return ccp if defined or acc_number """
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': 'R 12312123',
            'isr_adherent_num': '1234567',
        })
        acc_num = bank_acc.get_account_number()
        self.assertEqual(acc_num, bank_acc.acc_number)
        bank_acc.ccp = '10-725-4'
        acc_num = bank_acc.get_account_number()
        self.assertEqual(acc_num, bank_acc.ccp)

    def test_create_bank_default_acc_number(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'bank_id': self.bank.id,
            'ccp': '46-110-7'
        })
        # account number set based on ccp
        self.assertEqual(bank_acc.acc_number, 'Camptocamp/CCP 46-110-7')
        self.assertEqual(bank_acc.ccp, '46-110-7')

    def test_onchange_post_bank_acc_number(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'bank_id': self.post_bank.id,
            'ccp': '46-110-7',
        })
        self.assertEqual(bank_acc.acc_number, 'Camptocamp/CCP 46-110-7')
        self.assertEqual(bank_acc.ccp, '46-110-7')
        # if it's postal update acc_number after the cpp number
        bank_acc.write({'ccp': '10-8060-7'})
        bank_acc.onchange_ccp_set_acc_number()
        self.assertEqual(bank_acc.acc_number, '10-8060-7')
        self.assertEqual(bank_acc.ccp, '10-8060-7')

    def test_onchange_post_bank_ccp_in_acc_number(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'bank_id': self.post_bank.id,
            'acc_number': '46-110-7',
            'ccp': None,
        })
        self.assertEqual(bank_acc.acc_number, '46-110-7')
        # on creation we don't compute ccp number
        self.assertFalse(bank_acc.ccp,)
        bank_acc.acc_number = '10-8060-7'
        bank_acc.onchange_acc_number_set_swiss_bank()
        bank_acc.onchange_bank_set_acc_number()
        # numbers recomputed
        self.assertEqual(bank_acc.acc_number, '10-8060-7')
        self.assertEqual(bank_acc.ccp, '10-8060-7')

    def test_name_search(self):
        self.bank.bic = 'BIC12345'
        result = self.env['res.bank'].name_search('BIC12345')
        self.assertEqual(result and result[0][0], self.bank.id)
        self.bank.code = 'CODE123'
        result = self.env['res.bank'].name_search('CODE123')
        self.assertEqual(result and result[0][0], self.bank.id)
        self.bank.street = 'Route de Neuchâtel'
        result = self.env['res.bank'].name_search('Route de Neuchâtel')
        self.assertEqual(result and result[0][0], self.bank.id)
        self.bank.city = 'Lausanne-Centre'
        result = self.env['res.bank'].name_search('Lausanne-Centre')
        self.assertEqual(result and result[0][0], self.bank.id)

    def test_multiple_ccp_number_for_same_partner(self):
        bank_acc = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': '46-110-7',
        })
        # each time this onchange triggered in UI it setup proper bank
        # and acc_number
        bank_acc.onchange_acc_number_set_swiss_bank()
        bank_acc.onchange_bank_set_acc_number()

        bank_acc2 = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': '46-110-7',
        })

        bank_acc2.onchange_acc_number_set_swiss_bank()
        bank_acc2.onchange_bank_set_acc_number()
        self.assertEqual(bank_acc2.bank_id, self.bank)
        self.assertEqual(bank_acc2.acc_number, 'Camptocamp/CCP 46-110-7 #1')
        self.assertEqual(bank_acc2.acc_type, 'bank')

        bank_acc3 = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': '46-110-7',
        })
        bank_acc3.onchange_acc_number_set_swiss_bank()
        bank_acc3.onchange_bank_set_acc_number()

        # no bank matches
        self.assertEqual(bank_acc3.bank_id, self.bank)
        self.assertEqual(bank_acc3.acc_number, 'Camptocamp/CCP 46-110-7 #2')
        self.assertEqual(bank_acc3.acc_type, 'bank')
        bank_acc.unlink()
        # next acc_numbers properly generated
        bank_acc4 = self.env['res.partner.bank'].create({
            'partner_id': self.partner.id,
            'acc_number': '46-110-7',
        })
        bank_acc4.onchange_acc_number_set_swiss_bank()
        bank_acc4.onchange_bank_set_acc_number()
        self.assertEqual(bank_acc4.acc_number, 'Camptocamp/CCP 46-110-7 #3')

    def test_acc_name_generation(self):
        # we test only proper name generation in different conditions
        bank_acc = self.env['res.partner.bank'].new({
            'acc_number': '46-110-7',
            'partner_id': False,
        })
        # acc_number is ok in first
        self.assertEqual(bank_acc.acc_number, '46-110-7')
        # but if some onchange trigger recompilation of name we flash any name
        # only it's not iban type
        bank_acc._update_acc_name()
        self.assertEqual(bank_acc.acc_number, '')
        # still no name
        bank_acc.partner_id = self.partner
        bank_acc._update_acc_name()
        self.assertEqual(bank_acc.acc_number, '')
        bank_acc.ccp = '46-110-7'
        bank_acc._update_acc_name()
        self.assertEqual(bank_acc.acc_number, 'Camptocamp/CCP 46-110-7')
        # remove partner name
        bank_acc.partner_id = ''
        bank_acc._update_acc_name()
        self.assertEqual(bank_acc.acc_number, 'CCP 46-110-7')
        # no changes for bank changes
        bank_acc.bank_id = self.bank
        bank_acc._update_acc_name()
        self.assertEqual(bank_acc.acc_number, 'CCP 46-110-7')
        # everything cleanup
        bank_acc.ccp = ''
        bank_acc._update_acc_name()
        self.assertEqual(bank_acc.acc_number, '')
