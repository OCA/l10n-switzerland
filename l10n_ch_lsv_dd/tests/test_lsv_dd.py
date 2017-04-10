# -*- coding: utf-8 -*-
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
from odoo import tools

from odoo.tests import SavepointCase
from odoo.modules.module import get_resource_path


class TestLsvDD(SavepointCase):

    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(
            cls.cr, 'account_asset',
            get_resource_path(module, *args),
            {}, 'init', False, 'test', cls.registry._assertion_report)

    @classmethod
    def setUpClass(cls):
        super(TestLsvDD, cls).setUpClass()
        cls._load('account', 'test', 'account_minimal_test.xml')
        cls.partner = cls.env.ref('base.res_partner_2')
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'bank')], limit=1)
        cls.account_receivable = cls.env['account.account'].search([(
            'user_type_id', '=', cls.env.ref(
                'account.data_account_type_receivable').id)], limit=1)
        cls.partner.property_account_receivable_id = cls.account_receivable
        cls.product_account = cls.env['account.account'].search([(
            'user_type_id', '=', cls.env.ref(
                'account.data_account_type_expenses').id)], limit=1)
        cls.product = cls.env.ref('product.product_product_10')

        # Payment modes
        cls.paymode_lsv = cls.env.ref('l10n_ch_lsv_dd.lsv_pay_mode')
        cls.paymode_lsv.fixed_journal_id.currency_id = cls.env.ref('base.EUR')
        cls.paymode_dd = cls.env.ref('l10n_ch_lsv_dd.dd_pay_mode')
        cls.paymode_dd.fixed_journal_id.currency_id = cls.env.ref('base.EUR')
        cls.paymode_dd_xml = cls.env.ref('l10n_ch_lsv_dd.dd_pay_mode_xml_dd')

        # Bank accounts
        cls.lsv_bank_account = cls.env.ref('l10n_ch_lsv_dd.company_bank_ubs')
        cls.dd_bank_account = cls.env.ref('l10n_ch_lsv_dd.company_bank_post')
        cls.dd_xml_bank_account = cls.env.ref(
            'l10n_ch_lsv_dd.company_bank_post_xml_dd')

        # Mandates
        cls.lsv_mandate = cls.env.ref('l10n_ch_lsv_dd.ubs_mandate')
        cls.dd_mandate = cls.env.ref('l10n_ch_lsv_dd.post_mandate')
        cls.dd_xml_mandate = cls.env.ref(
            'l10n_ch_lsv_dd.post_mandate_xml_dd')

        # Create some invoices that will be included in payment orders
        cls.lsv_invoice = cls.create_invoice(
            cls.paymode_lsv.id,
            cls.lsv_bank_account.id,
            cls.lsv_mandate.id,
            42)
        cls.dd_invoice = cls.create_invoice(
            cls.paymode_dd.id,
            cls.dd_bank_account.id,
            cls.dd_mandate.id,
            48)
        cls.dd_xml_invoice = cls.create_invoice(
            cls.paymode_dd_xml.id,
            cls.dd_xml_bank_account.id,
            cls.dd_xml_mandate.id,
            56)

    @classmethod
    def create_invoice(cls, payment_mode_id, partner_bank_id, mandate_id,
                       amount):
        """
        Utility to quickly create an invoice
        """
        vals = {
            'company_id': cls.env.ref('base.main_company').id,
            'journal_id': cls.journal.id,
            'currency_id': cls.env.ref('base.EUR').id,
            'account_id': cls.account_receivable.id,
            'type': 'out_invoice',
            'partner_id': cls.partner.id,
            'date_invoice': fields.Date.today(),
            'partner_bank_id': partner_bank_id,
            'mandate_id': mandate_id,
            'bvr_reference': '42564984',
            'payment_mode_id': payment_mode_id,
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'account_id': cls.product_account.id,
                'name': cls.product.name,
                'price_unit': amount,
                'quantity': 1,
            })]
        }
        invoice = cls.env['account.invoice'].create(vals)
        invoice.action_invoice_open()
        return invoice

    def create_payment_order(self, payment_mode, move_line, bank_id,
                             partner_bank_id, mandate_id):
        return self.env['account.payment.order'].create({
            'date_prefered': 'due',
            'payment_mode_id': payment_mode.id,
            'journal_id': payment_mode.fixed_journal_id.id,
            'company_partner_bank_id': bank_id,
            'payment_type': 'inbound',
            'state': 'draft',
            'payment_line_ids': [(0, 0, {
                'move_line_id': move_line.id,
                'amount_currency': move_line.debit,
                'currency_id': self.env.ref('base.EUR').id,
                'partner_id': self.partner.id,
                'partner_bank_id': partner_bank_id,
                'mandate_id': mandate_id,
                'communictation_type': 'normal',
                'communication': '42564984'
            })],
            'currency': 'EUR'
        })

    def test_lsv_payment_order(self):
        """
        Test the generation of a LSV payment file
        """
        move_line = self.lsv_invoice.move_id.line_ids[0]
        pay_order = self.create_payment_order(
            self.paymode_lsv, move_line, self.lsv_bank_account.id,
            self.env.ref('l10n_ch_lsv_dd.partner_bank_ubs').id,
            self.lsv_mandate.id
        )
        pay_order.draft2open()
        result = pay_order.open2generated()
        attachment_id = result.get('res_id')
        self.assertTrue(attachment_id)
        attachment = self.env['ir.attachment'].browse(attachment_id)
        self.assertTrue(attachment.datas)

    def test_dd_payment_order(self):
        """
        Test the generation of a DD payment file
        """
        move_line = self.dd_invoice.move_id.line_ids[0]
        pay_order = self.create_payment_order(
            self.paymode_dd, move_line, self.dd_bank_account.id,
            self.env.ref('l10n_ch_lsv_dd.partner_bank_post').id,
            self.dd_mandate.id
        )
        pay_order.draft2open()
        result = pay_order.open2generated()
        attachment_id = result.get('res_id')
        self.assertTrue(attachment_id)
        attachment = self.env['ir.attachment'].browse(attachment_id)
        self.assertTrue(attachment.datas)

    def test_dd_xml_payment_order(self):
        """
        Test the generation of a DD XML payment file
        """
        move_line = self.dd_xml_invoice.move_id.line_ids[0]
        pay_order = self.create_payment_order(
            self.paymode_dd_xml, move_line, self.dd_xml_bank_account.id,
            self.env.ref('l10n_ch_lsv_dd.partner_bank_post_xml_dd').id,
            self.dd_xml_mandate.id
        )
        pay_order.draft2open()
        result = pay_order.open2generated()
        attachment_id = result.get('res_id')
        self.assertTrue(attachment_id)
        attachment = self.env['ir.attachment'].browse(attachment_id)
        self.assertTrue(attachment.datas)
