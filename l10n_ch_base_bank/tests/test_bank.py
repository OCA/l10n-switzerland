# Copyright 2014-2015 Nicolas Bessi (Azure Interior SA)
# Copyright 2015-2017 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import common
from odoo.tools import mute_logger
from odoo import exceptions
from odoo.tests.common import Form
from odoo.tests import tagged

ch_iban = 'CH15 3881 5158 3845 3843 7'
ch_post_iban = 'CH09 0900 0000 1000 8060 7'
fr_iban = 'FR83 8723 4133 8709 9079 4002 530'


@tagged('post_install', '-at_install')
class TestBank(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref('base.res_partner_12')
        cls.bank = cls.env['res.bank'].create({
            'name': 'Alternative Bank Schweiz AG',
            'bic': 'ALSWCH21XXX',
            'clearing': '38815',
            'ccp': '46-110-7',
        })
        cls.post_bank = cls.env['res.bank'].search(
            [('bic', '=', 'POFICHBEXXX')])
        if not cls.post_bank:
            cls.post_bank = cls.env['res.bank'].create({
                'name': 'PostFinance AG',
                'bic': 'POFICHBEXXX',
                'clearing': '9000',
                'ccp': '10-8060-7',
            })

    def new_form(self):
        form = Form(
            self.env['res.partner.bank'],
            view='l10n_ch_base_bank.add_ccp_on_res_partner_bank'
        )
        form.partner_id = self.partner
        return form

    def new_empty_form(self):
        # in some cases we need form without partner
        form = Form(
            self.env['res.partner.bank'],
            view='l10n_ch_base_bank.add_ccp_on_res_partner_bank'
        )
        return form

    def test_bank_iban(self):

        bank_acc = self.new_form()
        bank_acc.acc_number = ch_iban.replace(' ', '')
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, ch_iban)
        self.assertEqual(account.ccp, '46-110-7')
        self.assertEqual(account.acc_type, 'iban')

    def test_bank_iban_with_spaces(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = ch_iban
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, ch_iban)
        self.assertEqual(account.ccp, '46-110-7')
        self.assertEqual(account.acc_type, 'iban')

    def test_bank_iban_lower_case(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = ch_iban.lower()
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, ch_iban.lower())
        self.assertEqual(account.ccp, '46-110-7')
        self.assertEqual(account.acc_type, 'iban')

    def test_bank_iban_foreign(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = fr_iban
        account = bank_acc.save()

        self.assertFalse(account.bank_id)
        self.assertEqual(account.acc_number, fr_iban)
        self.assertFalse(account.ccp)
        self.assertEqual(account.acc_type, 'iban')

    def test_bank_ccp(self):
        # test UI onchange methods
        bank_acc = self.new_form()
        bank_acc.acc_number = '46-110-7'
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, 'Azure Interior/CCP 46-110-7')
        self.assertEqual(account.ccp, '46-110-7')
        self.assertEqual(account.acc_type, 'bank')

    def test_bank_ccp_no_found(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = '10-8060-7'
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        # if acc_number given by user don't update it
        self.assertEqual(account.acc_number, '10-8060-7')
        self.assertEqual(account.ccp, '10-8060-7')
        self.assertEqual(account.acc_type, 'postal')

        bank_acc.bank_id = self.post_bank
        bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        # copied ccp to acc_number
        self.assertEqual(account.acc_number, '10-8060-7')
        self.assertEqual(account.ccp, '10-8060-7')
        self.assertEqual(account.acc_type, 'postal')

    def test_ccp(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = '10-8060-7'
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, '10-8060-7')
        self.assertEqual(account.ccp, '10-8060-7')
        self.assertEqual(account.acc_type, 'postal')

    def test_iban_ccp(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = ch_post_iban
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, ch_post_iban)
        self.assertEqual(account.ccp, '10-8060-7')
        self.assertEqual(account.acc_type, 'iban')

    def test_other_bank(self):
        self.bank.ccp = False
        bank_acc = self.new_form()
        # the sequence is important
        bank_acc.bank_id = self.bank
        bank_acc.acc_number = 'R 12312123'
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, 'R 12312123')
        self.assertEqual(account.ccp, False)
        self.assertEqual(account.acc_type, 'bank')

    def test_set_ccp(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = None
        bank_acc.acc_number = '10-8060-7'
        account = bank_acc.save()

        self.assertEqual(account.acc_number, '10-8060-7')
        self.assertEqual(account.bank_id, self.post_bank)

    def test_set_ccp_bank(self):
        # we create bank account
        # action runs in UI before creation
        bank_acc = self.new_form()
        bank_acc.acc_number = None
        bank_acc.ccp = '10-8060-7'
        bank_acc.bank_id = self.bank
        account = bank_acc.save()

        # in result we should get new ccp number as we have bank_id and
        # this he has ccp, new acc_number

        self.assertEqual(account.acc_number,
                         'Azure Interior/CCP 10-8060-7')
        self.assertEqual(account.ccp, '10-8060-7')
        self.assertEqual(account.bank_id, self.bank)

    def test_set_onchange_ccp_post(self):
        # fond bank based on ccp set acc_number
        # action runs in UI before creation
        bank_acc = self.new_form()
        bank_acc.ccp = '10-8060-7'
        account = bank_acc.save()

        self.assertEqual(account.acc_number, '10-8060-7')
        self.assertEqual(account.ccp, '10-8060-7')
        self.assertEqual(account.bank_id, self.post_bank)

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

    def test_create_bank_default_acc_number(self):
        bank_acc = self.new_form()
        bank_acc.bank_id = self.bank
        bank_acc.ccp = '46-110-7'
        account = bank_acc.save()

        # account number set based on ccp
        self.assertEqual(account.acc_number, 'Azure Interior/CCP 46-110-7')
        self.assertEqual(account.ccp, '46-110-7')

    def test_onchange_post_bank_acc_number(self):
        bank_acc = self.new_empty_form()
        bank_acc.bank_id = self.post_bank
        bank_acc.ccp = '10-8060-7'

        self.assertEqual(bank_acc.ccp, '10-8060-7')
        self.assertEqual(bank_acc.acc_number, '10-8060-7')

        # if it's postal update acc_number after the cpp number
        bank_acc.ccp = '46-110-7'
        self.assertEqual(bank_acc.acc_number, 'CCP 46-110-7')

        bank_acc.partner_id = self.partner
        self.assertEqual(bank_acc.acc_number, 'Azure Interior/CCP 46-110-7')
        self.assertEqual(bank_acc.ccp, '46-110-7')

    def test_onchange_post_bank_ccp_in_acc_number(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = '46-110-7'
        bank_acc.bank_id = self.post_bank

        self.assertEqual(bank_acc.ccp, '46-110-7')
        self.assertEqual(bank_acc.acc_number, '46-110-7')

    def test_name_search(self):
        self.bank.bic = 'BBAVBEBB'
        result = self.env['res.bank'].name_search('BBAVBEBB')
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
        bank_acc = self.new_form()
        bank_acc.acc_number = '46-110-7'
        bank_acc.save()
        bank_acc_2 = self.new_form()
        bank_acc_2.acc_number = '46-110-7'
        account2 = bank_acc_2.save()

        self.assertEqual(account2.bank_id, self.bank)
        self.assertEqual(account2.acc_number,
                         'Azure Interior/CCP 46-110-7 #1')
        self.assertEqual(account2.acc_type, 'bank')

        bank_acc_3 = self.new_form()
        bank_acc_3.acc_number = '46-110-7'
        account3 = bank_acc_3.save()

        # no bank matches
        self.assertEqual(account3.bank_id, self.bank)
        self.assertEqual(account3.acc_number,
                         'Azure Interior/CCP 46-110-7 #2')
        self.assertEqual(account3.acc_type, 'bank')
        account3.unlink()
        # next acc_numbers properly generated

        bank_acc_4 = self.new_form()
        bank_acc_4.acc_number = '46-110-7'
        account4 = bank_acc_4.save()

        account4.onchange_acc_number_set_swiss_bank()
        account4.onchange_bank_set_acc_number()
        self.assertEqual(account4.acc_number,
                         'Azure Interior/CCP 46-110-7 #3')

    def test_acc_name_generation(self):
        # this test runs directly with object and onchange methods as Form
        # class has constrains to flash required field as partner_id is
        # once is set we can only replace on other partner but in view form
        # we can make such actions

        # we test only proper name generation in different conditions
        account = self.env['res.partner.bank'].new({
            'acc_number': '46-110-7',
            'partner_id': False,
        })
        # acc_number is ok in first
        self.assertEqual(account.acc_number, '46-110-7')
        # but if some onchange trigger recompilation of name we flash any name
        # only it's not iban type
        account._update_acc_name()
        self.assertEqual(account.acc_number, '')
        # still no name
        account.partner_id = self.partner
        account._update_acc_name()
        self.assertEqual(account.acc_number, '')
        account.ccp = '46-110-7'
        account._update_acc_name()
        self.assertEqual(account.acc_number, 'Azure Interior/CCP 46-110-7')
        # remove partner name
        account.partner_id = ''
        account._update_acc_name()
        self.assertEqual(account.acc_number, 'CCP 46-110-7')
        # no changes for bank changes
        account.bank_id = self.bank
        account._update_acc_name()
        self.assertEqual(account.acc_number, 'CCP 46-110-7')
        # everything cleanup
        account.ccp = ''
        account._update_acc_name()
        self.assertEqual(account.acc_number, '')
