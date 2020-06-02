# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import common

CH_POSTAL = "10-8060-7"
CH_SUBSCRIPTION = "01-162-8"


class TestBankType(common.SavepointCase):
    def test_is_bank_account_with_isr_issuer(self):
        bank = self.env["res.bank"].create(
            {"name": "BCV", "bic": "BCVLCH2LXXX", "clearing": "234234"}
        )
        bank_account = self.env["res.partner.bank"].create(
            {
                "partner_id": self.partner.id,
                "bank_id": bank.id,
                "acc_number": "ISR 01-1234-1",
                "l10n_ch_postal": CH_SUBSCRIPTION,
            }
        )
        self.assertEqual(bank_account.acc_type, "bank")

    def test_is_postal_account(self):
        bank = self.env["res.bank"].create(
            {"name": "BCV", "bic": "BCVLCH2LXXX", "clearing": "234234"}
        )
        bank_account = self.env["res.partner.bank"].create(
            {
                "partner_id": self.partner.id,
                "bank_id": bank.id,
                "acc_number": CH_POSTAL,
                "l10n_ch_postal": CH_POSTAL,
            }
        )
        self.assertEqual(bank_account.acc_type, "postal")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env.ref("base.main_partner")
