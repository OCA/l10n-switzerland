##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2017 Emanuel Cino
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

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestLsvDD(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref="l10n_ch.l10nch_chart_template"):
        super().setUpClass(chart_template_ref)
        cls.env.company.initiating_party_identifier = "CH1312300000012345"
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "CH63 0900 0000 2500 9779 8",
                "partner_id": cls.partner.id,
                "acc_type": "postal",
                "bank_id": cls.env.ref("l10n_ch_base_bank.bank_postfinance").id,
            }
        )
        cls.bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "CH10 0900 0000 2500 9778 2",
                "partner_id": cls.env.company.partner_id.id,
                "acc_type": "postal",
                "bank_id": cls.env.ref("l10n_ch_base_bank.bank_postfinance").id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "DD for test",
                "type": "bank",
                "bank_account_id": cls.bank.id,
            }
        )
        cls.account_receivable = cls.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_receivable").id,
                )
            ],
            limit=1,
        )
        cls.partner.property_account_receivable_id = cls.account_receivable
        cls.product = cls.env.ref("product.product_product_10")
        # Payment mode
        cls.paymode_dd_xml = cls.env["account.payment.mode"].create(
            {
                "name": "DD XML for test",
                "payment_type": "inbound",
                "fixed_journal_id": cls.journal.id,
                "bank_account_link": "fixed",
                "payment_order_ok": True,
                "payment_method_id": cls.env.ref(
                    "l10n_ch_pain_direct_debit.export_sepa_dd"
                ).id,
            }
        )
        # Mandate
        cls.dd_xml_mandate = cls.env["account.banking.mandate"].create(
            {
                "partner_id": cls.partner.id,
                "state": "valid",
                "partner_bank_id": cls.partner_bank.id,
                "signature_date": fields.Date.today(),
                "type": "recurrent",
                "recurrent_sequence_type": "first",
            }
        )
        cls.dd_xml_invoice = cls.init_invoice(
            "out_invoice",
            cls.partner,
            fields.Date.today(),
            True,
            cls.product,
            [56],
            currency=cls.env.ref("base.EUR"),
        )

    def create_payment_order(
        self, payment_mode, move_line, bank_id, partner_bank_id, mandate_id
    ):
        return self.env["account.payment.order"].create(
            {
                "date_prefered": "due",
                "payment_mode_id": payment_mode.id,
                "journal_id": payment_mode.fixed_journal_id.id,
                "company_partner_bank_id": bank_id,
                "payment_type": "inbound",
                "state": "draft",
                "payment_line_ids": [
                    (
                        0,
                        0,
                        {
                            "move_line_id": move_line.id,
                            "amount_currency": move_line.debit,
                            "currency_id": self.env.ref("base.EUR").id,
                            "partner_id": self.partner.id,
                            "partner_bank_id": partner_bank_id,
                            "mandate_id": mandate_id,
                            "communication_type": "normal",
                            "communication": "42564984",
                            "local_instrument": "DDCOR1",
                        },
                    )
                ],
            }
        )

    def test_dd_xml_payment_order_generates_correct_attachment(self):
        """
        Test the generation of a DD XML payment file
        """
        move_line = self.dd_xml_invoice.line_ids[0]
        pay_order = self.create_payment_order(
            self.paymode_dd_xml,
            move_line,
            self.bank.id,
            self.partner_bank.id,
            self.dd_xml_mandate.id,
        )
        pay_order.draft2open()
        result = pay_order.open2generated()
        attachment_id = result.get("res_id")
        self.assertTrue(attachment_id, "No attachment ID returned")
        attachment = self.env["ir.attachment"].browse(attachment_id)
        self.assertTrue(attachment.datas, "No data in attachment")

    def test_dd_xml_payment_order_state_changes(self):
        """
        Test the state changes of a DD XML payment order
        """
        move_line = self.dd_xml_invoice.line_ids[0]
        pay_order = self.create_payment_order(
            self.paymode_dd_xml,
            move_line,
            self.bank.id,
            self.partner_bank.id,
            self.dd_xml_mandate.id,
        )
        self.assertEqual(pay_order.state, "draft", "Initial state is not 'draft'")
        pay_order.draft2open()
        self.assertEqual(pay_order.state, "open", "State did not change to 'open'")
        pay_order.open2generated()
        self.assertEqual(
            pay_order.state, "generated", "State did not change to 'generated'"
        )
