# Copyright 2015-2017 Yannick Vaucher
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.tests.common import Form


class TestBank(common.SavepointCase):

    def test_get_account_number(self):
        # get_account_number return ccp if defined or acc_number
        bank_acc = Form(
            self.env['res.partner.bank'],
            view='l10n_ch_base_bank.add_ccp_on_res_partner_bank'
        )
        bank_acc.partner_id = self.env.ref('base.res_partner_12')

        bank_acc.acc_number = 'R 12312123'
        bank_acc.isr_adherent_num = '1234567'
        account = bank_acc.save()

        acc_num = account.get_account_number()
        self.assertEqual(acc_num, account.acc_number)
        account.ccp = '10-725-4'
        acc_num = account.get_account_number()
        self.assertEqual(acc_num, account.ccp)
