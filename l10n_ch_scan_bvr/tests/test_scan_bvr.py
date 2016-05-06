# -*- coding: utf-8 -*-
# Author: Yannick Vaucher
# (c) 2014 Camptocamp SA
# (c) 2015 Alex Comba - Agile Business Group
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import openerp.tests.common as common


class TestScanBvr(common.TransactionCase):
    """ Test the wizard for bvr line scanning """

    def setUp(self):
        super(TestScanBvr, self).setUp()
        self.ScanBVR = self.env['scan.bvr']

        #  I create a swiss bank with a BIC number
        Bank = self.env['res.bank']
        PartnerBank = self.env['res.partner.bank']
        bank1 = Bank.create({
            'name': 'Big swiss bank',
            'bic': 'DRESDEFF300',
            'country': self.ref('base.ch'),
        })
        self.partner1 = self.env.ref('base.res_partner_2')
        tax22 = self.env['account.tax'].create({
            'name': '22%',
            'amount': 0.22,
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
            'state': 'bank',
            'name': 'Account',
            'bank': bank1.id,
            'acc_number': 'CH9100767000S00023455',
            'partner_id': self.ref('base.res_partner_2'),
        })
        self.partner1bank1 = PartnerBank.browse(partner1bank1.id)
        self.purchase_journal_id = self.ref('account.expenses_journal')

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
        act = wizard.validate_bvr_string()
        self.assertTrue(act['res_id'])

        new_invoice = self.env['account.invoice'].browse(act['res_id'])
        self.assertAlmostEqual(3949.75, new_invoice.amount_total, places=2)
