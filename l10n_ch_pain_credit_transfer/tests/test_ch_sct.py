# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import fields
from odoo.tests.common import SavepointCase
from odoo.tools import float_compare

ch_iban = "CH15 3881 5158 3845 3843 7"


class TestSCTCH(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.main_company = cls.env.ref("base.main_company")
        cls.partner_2 = cls.env.ref("base.res_partner_2")

        Account = cls.env["account.account"]
        Journal = cls.env["account.journal"]
        PaymentMode = cls.env["account.payment.mode"]

        cls.payment_order_model = cls.env["account.payment.order"]
        cls.payment_line_model = cls.env["account.payment.line"]
        cls.bank_line_model = cls.env["bank.payment.line"]
        cls.partner_bank_model = cls.env["res.partner.bank"]
        cls.attachment_model = cls.env["ir.attachment"]

        cls.account_expense = Account.create(
            {
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
                "name": "Test expense account",
                "code": "TEA",
                "company_id": cls.main_company.id,
            }
        )
        cls.account_payable = Account.create(
            {
                "user_type_id": cls.env.ref("account.data_account_type_payable").id,
                "name": "Test payable account",
                "code": "TTA",
                "company_id": cls.main_company.id,
                "reconcile": True,
            }
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
                "partner_id": cls.env.ref("base.main_partner").id,
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
        cls.partner_bank = cls.partner_bank_model.create(
            {
                "acc_number": "CH9100767000S00023455",
                "partner_id": cls.partner_2.id,
                "bank_id": ch_bank2.id,
                "l10n_ch_postal": "01-1234-1",
            }
        )

    def test_sct_ch_payment_type1(self):
        invoice1 = self.create_invoice(
            self.partner_2.id,
            self.partner_bank.id,
            self.eur_currency,
            42.0,
            "132000000000000000000000014",
        )
        invoice2 = self.create_invoice(
            self.partner_2.id,
            self.partner_bank.id,
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
                ("partner_id", "=", self.partner_2.id),
                ("order_id", "=", self.payment_order.id),
            ]
        )
        self.assertEqual(len(pay_lines), 2)
        pay_line1 = pay_lines[0]
        accpre = self.env["decimal.precision"].precision_get("Account")
        self.assertEqual(pay_line1.currency_id, self.eur_currency)
        self.assertEqual(pay_line1.partner_bank_id, invoice1.partner_bank_id)
        self.assertEqual(
            float_compare(pay_line1.amount_currency, 42, precision_digits=accpre),
            0,
        )
        self.assertEqual(pay_line1.communication_type, "isr")
        self.assertEqual(pay_line1.communication, "132000000000000000000000014")
        self.payment_order.draft2open()
        self.assertEqual(self.payment_order.state, "open")
        self.assertEqual(self.payment_order.sepa, False)
        bank_lines = self.bank_line_model.search(
            [("partner_id", "=", self.partner_2.id)]
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
            "http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd",
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
            self.assertEqual(inv.payment_state, "paid")
        return

    def test_sct_ch_payment_type3(self):
        invoice1 = self.create_invoice(
            self.partner_2.id,
            self.partner_bank.id,
            self.eur_currency,
            4042.0,
            "Inv1242",
        )
        invoice2 = self.create_invoice(
            self.partner_2.id,
            self.partner_bank.id,
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
                ("partner_id", "=", self.partner_2.id),
                ("order_id", "=", self.payment_order.id),
            ]
        )
        self.assertEqual(len(pay_lines), 2)
        pay_line1 = pay_lines[0]
        accpre = self.env["decimal.precision"].precision_get("Account")
        self.assertEqual(pay_line1.currency_id, self.eur_currency)
        self.assertEqual(pay_line1.partner_bank_id, invoice1.partner_bank_id)
        self.assertEqual(
            float_compare(pay_line1.amount_currency, 4042.0, precision_digits=accpre),
            0,
        )
        self.assertEqual(pay_line1.communication_type, "normal")
        self.assertEqual(pay_line1.communication, "Inv1242")
        self.payment_order.draft2open()
        self.assertEqual(self.payment_order.state, "open")
        self.assertEqual(self.payment_order.sepa, False)
        bank_lines = self.bank_line_model.search(
            [("partner_id", "=", self.partner_2.id)]
        )
        self.assertEqual(len(bank_lines), 1)
        bank_line = bank_lines[0]
        self.assertEqual(bank_line.currency_id, self.eur_currency)
        self.assertEqual(bank_line.communication_type, "normal")
        self.assertEqual(bank_line.communication, "Inv1242-Inv1248")
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
            "http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd",
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
            self.assertEqual(inv.payment_state, "paid")
        return

    @classmethod
    def create_invoice(
        cls,
        partner_id,
        partner_bank_id,
        currency_id,
        price_unit,
        reference,
        move_type="in_invoice",
    ):
        data = {
            "partner_id": partner_id,
            "reference_type": "none",
            "ref": reference,
            "currency_id": currency_id.id,
            "invoice_date": fields.Date.today(),
            "move_type": move_type,
            "payment_mode_id": cls.payment_mode.id,
            "partner_bank_id": partner_bank_id,
            "invoice_line_ids": [],
        }
        line_data = {
            "name": "Great service",
            "account_id": cls.account_expense.id,
            "price_unit": price_unit,
            "quantity": 1,
        }
        data["invoice_line_ids"].append((0, 0, line_data))
        inv = cls.env["account.move"].create(data)
        inv.action_post()
        return inv
