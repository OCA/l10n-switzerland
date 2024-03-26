# Copyright 2014-2015 Nicolas Bessi (Azure Interior SA)
# Copyright 2015-2019 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase

CH_IBAN = "CH15 3881 5158 3845 3843 7"
CH_POSTFINANCE_IBAN = "CH09 0900 0000 1000 8060 7"
FR_IBAN = "FR83 8723 4133 8709 9079 4002 530"


@tagged("post_install", "-at_install")
class TestBank(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.bank = cls.env["res.bank"].create(
            {
                "name": "Alternative Bank Schweiz AG",
                "bic": "ALSWCH21XXX",
                "clearing": "38815",
            }
        )
        cls.post_bank = cls.env["res.bank"].search([("bic", "=", "POFICHBEXXX")])
        if not cls.post_bank:
            cls.post_bank = cls.env["res.bank"].create(
                {"name": "PostFinance AG", "bic": "POFICHBEXXX", "clearing": "9000"}
            )

    def new_form(self):
        form = Form(
            self.env["res.partner.bank"],
            view="l10n_ch.isr_partner_bank_form",
        )
        form.partner_id = self.partner
        return form

    def new_empty_form(self):
        # in some cases we need form without partner
        form = Form(
            self.env["res.partner.bank"],
            view="l10n_ch.isr_partner_bank_form",
        )
        return form

    def test_bank_iban(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_IBAN.replace(" ", "")
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, CH_IBAN)
        self.assertEqual(account.acc_type, "iban")

    def test_bank_iban_with_spaces(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_IBAN
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, CH_IBAN)
        self.assertEqual(account.acc_type, "iban")

    def test_bank_iban_lower_case(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_IBAN.lower()
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, CH_IBAN.lower())
        self.assertEqual(account.acc_type, "iban")

    def test_bank_iban_foreign(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = FR_IBAN
        account = bank_acc.save()

        self.assertFalse(account.bank_id)
        self.assertEqual(account.acc_number, FR_IBAN)
        self.assertEqual(account.acc_type, "iban")

    def test_iban_postal(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTFINANCE_IBAN.replace(" ", "")
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, CH_POSTFINANCE_IBAN)
        self.assertEqual(account.acc_type, "iban")

    def test_iban_postal_with_spaces(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTFINANCE_IBAN
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, CH_POSTFINANCE_IBAN)
        self.assertEqual(account.acc_type, "iban")

    def test_iban_postal_lower_case(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTFINANCE_IBAN.lower()
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, CH_POSTFINANCE_IBAN.lower())
        self.assertEqual(account.acc_type, "iban")

    def test_other_bank(self):
        bank_acc = self.new_form()
        # the sequence is important
        bank_acc.bank_id = self.bank
        bank_acc.acc_number = "R 12312123"
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, "R 12312123")
        self.assertEqual(account.acc_type, "bank")

    def test_name_search(self):
        self.bank.bic = "BBAVBEBB"
        result = self.env["res.bank"].name_search("BBAVBEBB")
        self.assertEqual(result and result[0][0], self.bank.id)
        self.bank.code = "CODE123"
        result = self.env["res.bank"].name_search("CODE123")
        self.assertEqual(result and result[0][0], self.bank.id)
        self.bank.street = "Route de Neuchâtel"
        result = self.env["res.bank"].name_search("Route de Neuchâtel")
        self.assertEqual(result and result[0][0], self.bank.id)
        self.bank.city = "Lausanne-Centre"
        result = self.env["res.bank"].name_search("Lausanne-Centre")
        self.assertEqual(result and result[0][0], self.bank.id)
