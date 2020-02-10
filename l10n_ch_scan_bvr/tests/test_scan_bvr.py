# -*- coding: utf-8 -*-
# Author: Yannick Vaucher
# Copyright 2014 Camptocamp SA
# Copyright 2015 Alex Comba - Agile Business Group
# Copyright 2016 Alvaro Estebanez - Brain-tec AG
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import openerp.tests.common as common
from odoo import tools
from odoo.modules.module import get_module_resource


class TestScanBvr(common.TransactionCase):
    """ Test the wizard for bvr line scanning """

    def _load(self, module, *args):
        tools.convert_file(self.cr, 'l10n_ch_scan_bvr',
                           get_module_resource(module, *args),
                           {}, 'init', False, 'test',
                           self.registry._assertion_report)

    def setUp(self):
        super(TestScanBvr, self).setUp()
        self._load('account', 'test', 'account_minimal_test.xml')
        self.ScanBVR = self.env['scan.bvr']

        #  I create a swiss bank with a BIC number
        Bank = self.env['res.bank']
        PartnerBank = self.env['res.partner.bank']
        bank1 = Bank.create({
            'name': 'Big swiss bank',
            'bic': 'DRESDEFF300',
            'country': self.ref('base.ch'),
            'ccp': 1234,
        })
        self.partner1 = self.env.ref('base.res_partner_2')
        tax22 = self.env['account.tax'].create({
            'name': '22%',
            'amount': 22,
            'price_include': True,
        })
        product1 = self.env['product.product'].create({
            'name': 'product1',
            'list_price': 10.00,
            'supplier_taxes_id': [(6, 0, [tax22.id])]
        })
        self.partner1.supplier_invoice_default_product = product1.id
        #  I create a bank account
        # ok this is an iban but base_iban might not be installed
        partner1bank1 = PartnerBank.create({
            'bank_id': bank1.id,
            'acc_number': 'CH9100767000S00023455',
            'partner_id': self.ref('base.res_partner_2'),
        })
        partner1bank2 = PartnerBank.create({
            'bank_id': bank1.id,
            'acc_number': 'Partner 2 01-40155-2',
            'partner_id': self.ref('base.res_partner_2'),
            'ccp': '01-40155-2',
            'bvr_adherent_num': '703192'
        })
        partner2bank1 = PartnerBank.create({
            'bank_id': bank1.id,
            'acc_number': 'Partner 3 01-40155-2',
            'partner_id': self.ref('base.res_partner_3'),
            'ccp': '01-40155-2',
            'bvr_adherent_num': '685234'
        })
        self.partner1bank1 = PartnerBank.browse(partner1bank1.id)
        self.partner1bank2 = PartnerBank.browse(partner1bank2.id)
        self.partner2bank1 = PartnerBank.browse(partner2bank1.id)
        self.purchase_journal_id = \
            self.ref('l10n_ch_scan_bvr.expenses_journal')

    def _test_00_action_scan_wrong_bvr(self):
        """ Check use of wrongly defined bvr line """
        bvr_string = '47045075054'
        wizard = self.ScanBVR.create({
            'bvr_string': bvr_string,
            'journal_id': self.purchase_journal_id,
        })
        try:
            wizard.validate_bvr_string()
        except:
            pass
        else:
            raise 'Missing error message for wrong BVR line'

    def test_01_action_scan_bvr(self):
        """ Check state of wizard passe in need information state
        if no partner has an adherent number equal to the one in
        bvr scan line

        0100003949753>120000000000234478943216899+ 010001628>

        """
        bvr_string = '0100003949753>120000000000234478943216899+ 010001628>'
        wizard = self.ScanBVR.create({
            'bvr_string': bvr_string,
            'journal_id': self.purchase_journal_id,
        })
        act = wizard.validate_bvr_string()
        self.assertEqual(wizard.state, 'need_extra_info')

        wizard.write({
            'partner_id': self.partner1.id,
            'bank_account_id': self.partner1bank1.id,
        })
        chf = self.env.ref('base.CHF')
        chf.active = True
        act = wizard.validate_bvr_string()
        self.assertTrue(act['res_id'])

        new_invoice = self.env['account.invoice'].browse(act['res_id'])
        self.assertAlmostEqual(3949.75, new_invoice.amount_total, places=2)

    def test_02_scan_2_banks(self):
        """ Check scan line when two bank accounts with same ccp
        and different bvr adherent numbers
        0100003949753>703192500010549027000209403+ 010401552>
        """
        bvr_string1 = '0100003949753>703192500010549027000209403+ 010401552>'
        wizard = self.ScanBVR.create({
            'bvr_string': bvr_string1,
            'journal_id': self.purchase_journal_id,
        })
        chf = self.env.ref('base.CHF')
        chf.active = True
        act = wizard.validate_bvr_string()
        self.assertTrue(act['res_id'])
        new_invoice = self.env['account.invoice'].browse(act['res_id'])
        self.assertTrue(
            new_invoice.partner_id.id == self.ref('base.res_partner_2'))
        self.assertAlmostEqual(3949.75, new_invoice.amount_total, places=2)
