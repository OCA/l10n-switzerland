# (c) 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from datetime import date

from lxml import etree

from odoo.tests import tagged
from odoo.tools import float_compare

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

ch_iban = "CH15 3881 5158 3845 3843 7"


@tagged("post_install", "-at_install")
class TestSCTCH(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref="l10n_ch.l10nch_chart_template"):
        super().setUpClass(chart_template_ref)
        Journal = cls.env["account.journal"]
        PaymentMode = cls.env["account.payment.mode"]
        Account = cls.env["account.account"]

        cls.payment_order_model = cls.env["account.payment.order"]
        cls.payment_line_model = cls.env["account.payment.line"]
        cls.partner_bank_model = cls.env["res.partner.bank"]
        cls.attachment_model = cls.env["ir.attachment"]
        cls.account_move_model = cls.env["account.move"]

        cls.partner_agrolait = cls.env.ref("base.res_partner_2")

        cls.account_expense = Account.search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_expenses").id,
                )
            ],
            limit=1,
        )
        cls.account_payable = Account.search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_payable").id,
                )
            ],
            limit=1,
        )
        # Create a swiss bank
        ch_bank1 = cls.env["res.bank"].create(
            {
                "name": "Alternative Bank Schweiz AG",
                "bic": "ALSWCH21XXX",
                "clearing": "38815",
            }
        )
        # create a ch bank account for my company
        cls.cp_partner_bank = cls.partner_bank_model.create(
            {
                "acc_number": ch_iban,
                "partner_id": cls.env.user.company_id.partner_id.id,
            }
        )
        cls.cp_partner_bank._onchange_acc_number_set_swiss_bank()
        # create journal
        cls.bank_journal = Journal.create(
            {
                "name": "Company Bank journal",
                "type": "bank",
                "code": "BNKFB",
                "bank_account_id": cls.cp_partner_bank.id,
                "bank_id": ch_bank1.id,
            }
        )
        # create a payment mode
        pay_method_id = cls.env.ref(
            "account_banking_sepa_credit_transfer.sepa_credit_transfer"
        ).id
        cls.payment_mode = PaymentMode.create(
            {
                "name": "CH credit transfer",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.bank_journal.id,
                "payment_method_id": pay_method_id,
            }
        )
        cls.payment_mode.payment_method_id.pain_version = "pain.001.001.03.ch.02"
        cls.chf_currency = cls.env.ref("base.CHF")
        cls.eur_currency = cls.env.ref("base.EUR")
        ch_bank2 = cls.env["res.bank"].create(
            {
                "name": "Banque Cantonale Vaudoise",
                "bic": "BCVLCH2LXXX",
                "clearing": "767",
            }
        )
        # Create a bank account with clearing 767
        cls.agrolait_partner_bank = cls.partner_bank_model.create(
            {
                "acc_number": "CH9100767000S00023455",
                "partner_id": cls.partner_agrolait.id,
                "bank_id": ch_bank2.id,
                "l10n_ch_postal": "01-1234-1",
            }
        )

    def test_sct_ch_payment_type1(self):
        invoice1 = self.create_invoice(
            self.partner_agrolait.id,
            self.agrolait_partner_bank.id,
            self.eur_currency,
            42.0,
            "132000000000000000000000014",
        )
        invoice2 = self.create_invoice(
            self.partner_agrolait.id,
            self.agrolait_partner_bank.id,
            self.eur_currency,
            12.0,
            "132000000000000000000000022",
        )
        for inv in [invoice1, invoice2]:
            action = inv.create_account_payment_line()
        self.assertEqual(action["res_model"], "account.payment.order")
        self.payment_order = self.payment_order_model.browse(action["res_id"])
        self.assertEqual(self.payment_order.payment_type, "outbound")
        self.assertEqual(self.payment_order.payment_mode_id, self.payment_mode)
        self.assertEqual(self.payment_order.journal_id, self.bank_journal)
        pay_lines = self.payment_line_model.search(
            [
                ("partner_id", "=", self.partner_agrolait.id),
                ("order_id", "=", self.payment_order.id),
            ]
        )
        self.assertEqual(len(pay_lines), 2)
        agrolait_pay_line1 = pay_lines[0]
        accpre = self.env["decimal.precision"].precision_get("Account")
        self.assertEqual(agrolait_pay_line1.currency_id, self.eur_currency)
        self.assertEqual(agrolait_pay_line1.partner_bank_id, invoice1.partner_bank_id)
        self.assertEqual(
            float_compare(
                agrolait_pay_line1.amount_currency, 42, precision_digits=accpre
            ),
            0,
        )
        self.assertEqual(agrolait_pay_line1.communication_type, "isr")
        self.assertEqual(
            agrolait_pay_line1.communication, "132000000000000000000000014"
        )
        self.payment_order.draft2open()
        self.assertEqual(self.payment_order.state, "open")
        self.assertEqual(self.payment_order.sepa, False)
        bank_lines = self.payment_line_model.search(
            [("partner_id", "=", self.partner_agrolait.id)]
        )
        self.assertEqual(len(bank_lines), 2)
        for bank_line in bank_lines:
            self.assertEqual(bank_line.currency_id, self.eur_currency)
            self.assertEqual(bank_line.communication_type, "isr")
            self.assertTrue(
                bank_line.communication
                in ["132000000000000000000000014", "132000000000000000000000022"]
            )
            self.assertEqual(bank_line.partner_bank_id, invoice1.partner_bank_id)

        action = self.payment_order.open2generated()
        self.assertEqual(self.payment_order.state, "generated")
        self.assertEqual(action["res_model"], "ir.attachment")
        attachment = self.attachment_model.browse(action["res_id"])
        self.assertEqual(attachment.name[-4:], ".xml")
        xml_file = base64.b64decode(attachment.datas)
        xml_root = etree.fromstring(xml_file)
        # print "xml_file=", etree.tostring(xml_root, pretty_print=True)
        namespaces = xml_root.nsmap
        namespaces["p"] = xml_root.nsmap[None]
        namespaces.pop(None)
        pay_method_xpath = xml_root.xpath("//p:PmtInf/p:PmtMtd", namespaces=namespaces)
        self.assertEqual(
            namespaces["p"],
            "http://www.six-interbank-clearing.com/de/" "pain.001.001.03.ch.02.xsd",
        )
        self.assertEqual(pay_method_xpath[0].text, "TRF")
        sepa_xpath = xml_root.xpath(
            "//p:PmtInf/p:PmtTpInf/p:SvcLvl/p:Cd", namespaces=namespaces
        )
        self.assertEqual(len(sepa_xpath), 0)
        local_instrument_xpath = xml_root.xpath(
            "//p:PmtInf/p:PmtTpInf/p:LclInstrm/p:Prtry", namespaces=namespaces
        )
        self.assertEqual(local_instrument_xpath[0].text, "CH01")

        debtor_acc_xpath = xml_root.xpath(
            "//p:PmtInf/p:DbtrAcct/p:Id/p:IBAN", namespaces=namespaces
        )
        self.assertEqual(
            debtor_acc_xpath[0].text,
            self.payment_order.company_partner_bank_id.sanitized_acc_number,
        )
        self.payment_order.generated2uploaded()
        self.assertEqual(self.payment_order.state, "uploaded")
        for inv in [invoice1, invoice2]:
            self.assertEqual(inv.state, "posted")
        return

    def test_sct_ch_payment_type3(self):
        invoice1 = self.create_invoice(
            self.partner_agrolait.id,
            self.agrolait_partner_bank.id,
            self.eur_currency,
            4042.0,
            "Inv1242",
        )
        invoice2 = self.create_invoice(
            self.partner_agrolait.id,
            self.agrolait_partner_bank.id,
            self.eur_currency,
            1012.55,
            "Inv1248",
        )
        for inv in [invoice1, invoice2]:
            action = inv.create_account_payment_line()
        self.assertEqual(action["res_model"], "account.payment.order")
        self.payment_order = self.payment_order_model.browse(action["res_id"])
        self.assertEqual(self.payment_order.payment_type, "outbound")
        self.assertEqual(self.payment_order.payment_mode_id, self.payment_mode)
        self.assertEqual(self.payment_order.journal_id, self.bank_journal)
        pay_lines = self.payment_line_model.search(
            [
                ("partner_id", "=", self.partner_agrolait.id),
                ("order_id", "=", self.payment_order.id),
            ]
        )
        self.assertEqual(len(pay_lines), 2)
        agrolait_pay_line1 = pay_lines[0]
        accpre = self.env["decimal.precision"].precision_get("Account")
        self.assertEqual(agrolait_pay_line1.currency_id, self.eur_currency)
        self.assertEqual(agrolait_pay_line1.partner_bank_id, invoice1.partner_bank_id)
        self.assertEqual(
            float_compare(
                agrolait_pay_line1.amount_currency,
                4042.0,
                precision_digits=accpre,
            ),
            0,
        )
        self.assertEqual(agrolait_pay_line1.communication_type, "normal")
        self.assertEqual(agrolait_pay_line1.communication, "Inv1242")
        self.payment_order.draft2open()
        self.assertEqual(self.payment_order.state, "open")
        self.assertEqual(self.payment_order.sepa, False)
        bank_lines = self.env["account.payment"].search(
            [("partner_id", "=", self.partner_agrolait.id)]
        )
        self.assertEqual(len(bank_lines), 1)
        bank_line = bank_lines[0]
        self.assertEqual(bank_line.currency_id, self.eur_currency)
        self.assertEqual(bank_line.payment_type, "outbound")
        self.assertEqual(bank_line.payment_reference, "Inv1242 - Inv1248")
        self.assertEqual(bank_line.partner_bank_id, invoice1.partner_bank_id)

        action = self.payment_order.open2generated()
        self.assertEqual(self.payment_order.state, "generated")
        self.assertEqual(action["res_model"], "ir.attachment")
        attachment = self.attachment_model.browse(action["res_id"])
        self.assertEqual(attachment.name[-4:], ".xml")
        xml_file = base64.b64decode(attachment.datas)
        xml_root = etree.fromstring(xml_file)
        # print "xml_file=", etree.tostring(xml_root, pretty_print=True)
        namespaces = xml_root.nsmap
        namespaces["p"] = xml_root.nsmap[None]
        namespaces.pop(None)
        pay_method_xpath = xml_root.xpath("//p:PmtInf/p:PmtMtd", namespaces=namespaces)
        self.assertEqual(
            namespaces["p"],
            "http://www.six-interbank-clearing.com/de/" "pain.001.001.03.ch.02.xsd",
        )
        self.assertEqual(pay_method_xpath[0].text, "TRF")
        sepa_xpath = xml_root.xpath(
            "//p:PmtInf/p:PmtTpInf/p:SvcLvl/p:Cd", namespaces=namespaces
        )
        self.assertEqual(len(sepa_xpath), 0)
        local_instrument_xpath = xml_root.xpath(
            "//p:PmtInf/p:PmtTpInf/p:LclInstrm/p:Prtry", namespaces=namespaces
        )
        self.assertEqual(len(local_instrument_xpath), 0)

        debtor_acc_xpath = xml_root.xpath(
            "//p:PmtInf/p:DbtrAcct/p:Id/p:IBAN", namespaces=namespaces
        )
        self.assertEqual(
            debtor_acc_xpath[0].text,
            self.payment_order.company_partner_bank_id.sanitized_acc_number,
        )
        self.payment_order.generated2uploaded()
        self.assertEqual(self.payment_order.state, "uploaded")
        for inv in [invoice1, invoice2]:
            self.assertEqual(inv.state, "posted")
        return

    def create_invoice(
        self,
        partner_id,
        partner_bank_id,
        currency,
        price_unit,
        ref,
        inv_type="in_invoice",
    ):
        invoice = self.account_move_model.create(
            {
                "partner_id": partner_id,
                "ref": ref,
                "currency_id": currency.id,
                "move_type": inv_type,
                "name": "/",
                "payment_mode_id": self.payment_mode.id,
                "partner_bank_id": partner_bank_id,
                "invoice_date": date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "price_unit": price_unit,
                            "quantity": 1,
                            "name": "Great service",
                            "account_id": self.account_expense.id,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice
