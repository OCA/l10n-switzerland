# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import TransactionCase


class TestSearchAccountMove(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.company_bank = cls.env["res.bank"].create(
            {"name": "BCV", "bic": "BBRUBEBB", "clearing": "234234"}
        )
        cls.company_partner_bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.company.partner_id.id,
                "bank_id": cls.company_bank.id,
                "acc_number": "ISR",
                "l10n_ch_isr_subscription_chf": "01-162-8",
                "sequence": 1,
            }
        )
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test Journal",
                "company_id": cls.company.id,
                "type": "sale",
                "code": "SALE123",
                "bank_id": cls.company_bank.id,
                "bank_acc_number": "10-8060-7",
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "partner_id": cls.partner.id,
                "journal_id": cls.journal.id,
                "move_type": "out_invoice",
            }
        )

    def assertFindRef(self, ref, operator, value, message=None):
        """Asserts that we can find the invoice

        Assuming the invoice has the given ``ref``, and that we perform a search
        on it's ``ref`` field with the given ``operator`` and ``value``.
        """
        self.invoice.ref = ref
        found = self.env["account.move"].search(
            [
                ("id", "in", self.invoice.ids),
                ("ref", operator, value),
            ],
        )
        self.assertEqual(self.invoice, found, message)

    def assertNotFindRef(self, ref, operator, value):
        """Asserts that we can't find the invoice

        Assuming the invoice has the given ``ref``, and that we perform a search
        on it's ``ref`` field with the given ``operator`` and ``value``.

        It's the direct opposite of :meth:`assertFindRef`.
        """
        self.invoice.ref = ref
        found = self.env["account.move"].search([("ref", operator, value)])
        self.assertFalse(found)

    def test_search_equal_strict(self):
        self.assertFindRef(
            "27 29990 00000 00001 70400 25019", "=", "27 29990 00000 00001 70400 25019"
        )

    def test_search_equal_whitespace_right(self):
        self.assertNotFindRef(
            "272999000000000017040025019", "=", "27 29990 00000 00001 70400 25019"
        )

    def test_search_equal_whitespace_left(self):
        self.assertNotFindRef(
            "27 29990 00000 00001 70400 25019", "=", "272999000000000017040025019"
        )

    def test_search_like_whitespace_right(self):
        self.assertFindRef("272999000000000017040025019", "like", "1 70400 25")

    def test_search_like_whitespace_left(self):
        self.assertFindRef("27 29990 00000 00001 70400 25019", "like", "17040025")

    def test_search_like_whitespace_both(self):
        self.assertFindRef("27 29990 00000 00001 70400 25019", "like", "17 040025 01")

    def test_search_eqlike_whitespace_raw(self):
        self.assertNotFindRef(
            "27 29990 00000 00001 70400 25019", "=like", "17 040025 01"
        )

    def test_search_eqlike_whitespace_wildcards(self):
        self.assertFindRef(
            "27 29990 00000 00001 70400 25019", "=like", "%17 040025 01%"
        )

    def test_search_different(self):
        self.assertNotFindRef("27 29990 00000 00001 70400 25019", "like", "4273473")

    def test_search_other_field(self):
        self.invoice.ref = "27 29990 00000 00001 70400 25019"
        found = self.env["account.move"].search([("partner_id", "=", self.partner.id)])
        self.assertIn(self.invoice, found)

    def test_search_unary_operator(self):
        self.invoice.ref = "27 29990 00000 00001 70400 25019"
        found = self.env["account.move"].search([("ref", "like", "2999000000")])
        self.assertIn(self.invoice, found)
