# Copyright 2014-2015 Nicolas Bessi (Azure Interior SA)
# Copyright 2015-2019 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import exceptions
from odoo.tests import tagged
from odoo.tests.common import Form, SavepointCase
from odoo.tools import mute_logger

CH_SUBSCRIPTION = "01-162-8"  # partner ISR subsr num we register under postal
CH_SUBSCRIPTION_9DIGITS = "010001628"  # same ISR subsr num in 9 digits format
CH_POSTAL = "10-8060-7"
CH_IBAN = "CH15 3881 5158 3845 3843 7"
CH_POSTFINANCE_IBAN = "CH09 0900 0000 1000 8060 7"
FR_IBAN = "FR83 8723 4133 8709 9079 4002 530"


@tagged("post_install", "-at_install")
class TestBank(SavepointCase):
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
        self.assertFalse(account.l10n_ch_postal)
        self.assertEqual(account.acc_type, "iban")

    def test_bank_iban_with_spaces(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_IBAN
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, CH_IBAN)
        self.assertFalse(account.l10n_ch_postal)
        self.assertEqual(account.acc_type, "iban")

    def test_bank_iban_lower_case(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_IBAN.lower()
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, CH_IBAN.lower())
        self.assertFalse(account.l10n_ch_postal)
        self.assertEqual(account.acc_type, "iban")

    def test_bank_iban_foreign(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = FR_IBAN
        account = bank_acc.save()

        self.assertFalse(account.bank_id)
        self.assertEqual(account.acc_number, FR_IBAN)
        self.assertFalse(account.l10n_ch_postal)
        self.assertEqual(account.acc_type, "iban")

    def test_bank_postal(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_SUBSCRIPTION
        bank_acc.bank_id = self.bank
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(
            account.acc_number,
            "ISR {} Azure Interior".format(CH_SUBSCRIPTION),
        )
        self.assertEqual(account.l10n_ch_postal, CH_SUBSCRIPTION)
        self.assertEqual(account.acc_type, "bank")

    def test_postal_set_bank_post(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTAL
        account = bank_acc.save()

        self.assertFalse(account.bank_id)
        # if acc_number given by user don't update it
        self.assertEqual(
            account.acc_number,
            CH_POSTAL,
        )
        self.assertEqual(account.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(account.acc_type, "postal")

        bank_acc.bank_id = self.post_bank
        bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, CH_POSTAL)
        self.assertEqual(account.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(account.acc_type, "postal")

    def test_postal_with_bank(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTAL
        bank_acc.bank_id = self.post_bank
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, CH_POSTAL)
        self.assertEqual(account.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(account.acc_type, "postal")

    def test_postal_without_bank(self):
        """It doesn't start with 01 or 03
        it is a postal account"""
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTAL
        account = bank_acc.save()

        self.assertFalse(account.bank_id)
        self.assertEqual(account.acc_number, CH_POSTAL)
        self.assertEqual(account.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(account.acc_type, "postal")

    def test_iban_postal(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTFINANCE_IBAN.replace(" ", "")
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, CH_POSTFINANCE_IBAN)
        self.assertEqual(account.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(account.acc_type, "iban")

    def test_iban_postal_with_spaces(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTFINANCE_IBAN
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, CH_POSTFINANCE_IBAN)
        self.assertEqual(account.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(account.acc_type, "iban")

    def test_iban_postal_lower_case(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_POSTFINANCE_IBAN.lower()
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.post_bank)
        self.assertEqual(account.acc_number, CH_POSTFINANCE_IBAN.lower())
        self.assertEqual(account.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(account.acc_type, "iban")

    def test_other_bank(self):
        bank_acc = self.new_form()
        # the sequence is important
        bank_acc.bank_id = self.bank
        bank_acc.acc_number = "R 12312123"
        account = bank_acc.save()

        self.assertEqual(account.bank_id, self.bank)
        self.assertEqual(account.acc_number, "R 12312123")
        self.assertEqual(account.l10n_ch_postal, False)
        self.assertEqual(account.acc_type, "bank")

    def test_set_postal_bank(self):
        # we create bank account
        # action runs in UI before creation
        bank_acc = self.new_form()
        # bank_acc.acc_number = None
        bank_acc.l10n_ch_postal = CH_POSTAL
        bank_acc.bank_id = self.bank
        account = bank_acc.save()

        # in result we should get new ccp number as we have bank_id and
        # this he has ccp, new acc_number

        self.assertEqual(account.acc_number, CH_POSTAL)
        self.assertEqual(account.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(account.bank_id, self.bank)

    def test_constraint_postal(self):
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.env["res.partner.bank"].create(
                    {
                        "partner_id": self.partner.id,
                        "bank_id": self.bank.id,
                        "acc_number": "R 12312123",
                        "l10n_ch_postal": "520-54025-54054",
                    }
                )

    def test_constraint_subscription_number(self):
        with self.assertRaises(exceptions.ValidationError):
            with mute_logger():
                self.env["res.partner.bank"].create(
                    {
                        "partner_id": self.partner.id,
                        "acc_number": "12312123",
                        "l10n_ch_isr_subscription_chf": "Not a valid number",
                    }
                )

        self.env["res.partner.bank"].create(
            {
                "partner_id": self.partner.id,
                "acc_number": "12312123",
                "l10n_ch_isr_subscription_chf": CH_SUBSCRIPTION,
            }
        )

        self.env["res.partner.bank"].create(
            {
                "partner_id": self.partner.id,
                "acc_number": "12312124",
                "l10n_ch_isr_subscription_chf": CH_SUBSCRIPTION_9DIGITS,
            }
        )

    def test_create_bank_default_acc_number(self):
        bank_acc = self.new_form()
        bank_acc.bank_id = self.bank
        bank_acc.l10n_ch_postal = CH_SUBSCRIPTION
        account = bank_acc.save()

        # account number set based on ccp
        self.assertEqual(
            account.acc_number,
            "ISR {} Azure Interior".format(CH_SUBSCRIPTION),
        )
        self.assertEqual(account.l10n_ch_postal, CH_SUBSCRIPTION)

    def test_onchange_post_bank_acc_number(self):
        """Check postal is copied to acc_number"""
        bank_acc = self.new_empty_form()
        bank_acc.bank_id = self.post_bank
        bank_acc.l10n_ch_postal = CH_POSTAL

        # if it's postal, copy the value in acc_number
        self.assertEqual(bank_acc.l10n_ch_postal, CH_POSTAL)
        self.assertEqual(bank_acc.acc_number, CH_POSTAL)

        # if it's ISR subscription, copy ISR + value in acc_number
        bank_acc.l10n_ch_postal = CH_SUBSCRIPTION
        self.assertEqual(
            bank_acc.acc_number,
            "ISR {}".format(CH_SUBSCRIPTION),
        )

        # if it's ISR subscription, copy ISR + value in acc_number
        # In this case we have the partner set
        bank_acc.partner_id = self.partner
        self.assertEqual(
            bank_acc.acc_number,
            "ISR {} Azure Interior".format(CH_SUBSCRIPTION),
        )
        self.assertEqual(bank_acc.l10n_ch_postal, CH_SUBSCRIPTION)

    def test_onchange_post_bank_isr_in_acc_number(self):
        """On entering ISR in acc_number

        Check acc_number is rewritten
        and ISR subscription number is copied in l10n_ch_postal

        """
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_SUBSCRIPTION
        bank_acc.bank_id = self.post_bank

        self.assertEqual(bank_acc.l10n_ch_postal, CH_SUBSCRIPTION)
        self.assertEqual(
            bank_acc.acc_number,
            "ISR {} Azure Interior".format(CH_SUBSCRIPTION),
        )

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

    def test_multiple_postal_number_for_same_partner(self):
        bank_acc = self.new_form()
        bank_acc.acc_number = CH_SUBSCRIPTION
        bank_acc.save()
        bank_acc_2 = self.new_form()
        bank_acc_2.acc_number = CH_SUBSCRIPTION
        account2 = bank_acc_2.save()

        self.assertFalse(account2.bank_id)
        self.assertEqual(
            account2.acc_number,
            "ISR {} Azure Interior #1".format(CH_SUBSCRIPTION),
        )
        self.assertEqual(account2.acc_type, "bank")

        bank_acc_3 = self.new_form()
        bank_acc_3.acc_number = CH_SUBSCRIPTION
        account3 = bank_acc_3.save()

        # no bank matches
        self.assertFalse(account3.bank_id)
        self.assertEqual(
            account3.acc_number,
            "ISR {} Azure Interior #2".format(CH_SUBSCRIPTION),
        )
        self.assertEqual(account3.acc_type, "bank")
        account3.unlink()
        # next acc_numbers properly generated

        # after deletion reuse same number
        bank_acc_4 = self.new_form()
        bank_acc_4.acc_number = CH_SUBSCRIPTION
        account4 = bank_acc_4.save()

        self.assertEqual(
            account4.acc_number,
            "ISR {} Azure Interior #2".format(CH_SUBSCRIPTION),
        )

    def test_acc_name_generation(self):
        # this test runs directly with object and onchange methods as Form
        # class has constrains to flash required field as partner_id is
        # once is set we can only replace on other partner but in view form
        # we can make such actions

        # we test only proper name generation in different conditions
        account = self.env["res.partner.bank"].new(
            {
                "acc_number": CH_SUBSCRIPTION,
                "partner_id": False,
                "l10n_ch_postal": False,
            }
        )
        # acc_number is ok in first
        self.assertEqual(account.acc_number, CH_SUBSCRIPTION)
        # but if some onchange trigger recompilation of name we flash any name
        # only it's not iban type
        account._update_acc_number()
        self.assertFalse(account.acc_number)
        # still no name
        account.partner_id = self.partner
        account._update_acc_number()
        self.assertFalse(account.acc_number)
        account.l10n_ch_postal = CH_SUBSCRIPTION
        account._update_acc_number()
        self.assertEqual(
            account.acc_number,
            "ISR {} Azure Interior".format(CH_SUBSCRIPTION),
        )
        # remove partner name
        account.partner_id = ""
        account._update_acc_number()
        self.assertEqual(account.acc_number, "ISR {}".format(CH_SUBSCRIPTION))
        # no changes for bank changes
        account.bank_id = self.bank
        account._update_acc_number()
        self.assertEqual(account.acc_number, "ISR {}".format(CH_SUBSCRIPTION))
        # everything cleanup
        account.l10n_ch_postal = ""
        account._update_acc_number()
        self.assertEqual(account.acc_number, "")
