# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import Form, TransactionCase


class TestCreateMove(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env.ref("base.res_partner_12")
        bank = cls.env["res.bank"].create(
            {"name": "BCV", "bic": "BBRUBEBB", "clearing": "234234"}
        )
        cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.company.partner_id.id,
                "bank_id": bank.id,
                "acc_number": "ISR",
                "l10n_ch_isr_subscription_chf": "01-162-8",
                "sequence": 1,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test Sale Journal",
                "company_id": cls.company.id,
                "type": "sale",
                "code": "SALE123",
                "bank_id": bank.id,
                "bank_acc_number": "01-1234-1",
            }
        )

    def new_form(self):
        inv = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        # Form(
        #     self.env['account.move'],
        #     view='account.view_move_form'
        # )
        inv.partner_id = self.partner
        inv.journal_id = self.journal
        return inv

    def test_emit_move_with_isr_ref(self):
        inv_form = self.new_form()
        move = inv_form.save()
        self.assertFalse(move._has_isr_ref())

        inv_form.ref = "132000000000000000000000014"
        inv_form.save()
        self.assertTrue(move._has_isr_ref())

    def test_emit_move_with_isr_ref_15_pos(self):
        inv_form = self.new_form()
        move = inv_form.save()

        self.assertFalse(move._has_isr_ref())

        move.ref = "132000000000004"
        # We consider such ref to be unstructured
        # and we shouldn't generate such refs
        self.assertFalse(move._has_isr_ref())

        # and save
        inv_form.save()

    def test_emit_move_with_non_isr_ref(self):
        inv_form = self.new_form()
        move = inv_form.save()

        self.assertFalse(move._has_isr_ref())

        move.ref = "Not a ISR ref with 27 chars"
        self.assertFalse(move._has_isr_ref())

    def test_emit_move_with_missing_isr_ref(self):
        inv_form = self.new_form()
        inv_form.save()
        inv_form.ref = False
        # and save
        move = inv_form.save()

        self.assertFalse(move._has_isr_ref())
