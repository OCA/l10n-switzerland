# -*- coding: utf-8 -*-
# Author: Yannick Vaucher
# (c) 2014 Camptocamp SA
# (c) 2015 Alex Comba - Agile Business Group
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import openerp.tests.common as common
from openerp.tools.float_utils import float_compare


class test_scan_bvr(common.TransactionCase):
    """ Test the wizard for bvr line scanning """

    def setUp(self):
        super(test_scan_bvr, self).setUp()
        cr, uid = self.cr, self.uid

        self.ScanBVR = self.registry('scan.bvr')

        #  I create a swiss bank with a BIC number
        Bank = self.registry('res.bank')
        Partner = self.registry('res.partner')
        PartnerBank = self.registry('res.partner.bank')
        self.Invoice = self.registry('account.invoice')
        bank1_id = Bank.create(
            cr,
            uid,
            {
                'name': 'Big swiss bank',
                'bic': 'DRESDEFF300',
                'country': self.ref('base.ch'),
            }
        )

        self.partner1 = Partner.browse(
            cr, uid, self.ref('base.res_partner_2'))
        #  I create a bank account
        # ok this is an iban but base_iban might not be installed
        partner1bank1_id = PartnerBank.create(
            cr,
            uid,
            {
                'state': 'bank',
                'name': 'Account',
                'bank': bank1_id,
                'acc_number': 'CH9100767000S00023455',
                'partner_id': self.ref('base.res_partner_2'),
            }
        )

        self.partner1bank1 = PartnerBank.browse(cr, uid, partner1bank1_id)
        self.purchase_journal_id = self.ref('account.expenses_journal')

    def test_00_action_scan_wrong_bvr(self):
        """ Check use of wrongly defined bvr line

        """
        cr, uid = self.cr, self.uid
        bvr_string = '47045075054'
        wizard_id = self.ScanBVR.create(
            cr,
            uid,
            {
                'bvr_string': bvr_string,
                'journal_id': self.purchase_journal_id,
            },
            context={}
        )
        try:
            self.ScanBVR.validate_bvr_string(
                cr, uid, [wizard_id], context={})
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
        cr, uid = self.cr, self.uid
        bvr_string = '0100003949753>120000000000234478943216899+ 010001628>'
        wizard_id = self.ScanBVR.create(
            cr, uid, {'bvr_string': bvr_string,
                      'journal_id': self.purchase_journal_id,
                      }, context={})
        act_win = self.ScanBVR.validate_bvr_string(
            cr, uid, [wizard_id], context={})
        wizard = self.ScanBVR.browse(
            cr, uid, wizard_id, context=None)
        assert wizard.state == 'need_extra_info'

        self.ScanBVR.write(
            cr,
            uid,
            wizard.id,
            {
                'partner_id': self.partner1.id,
                'bank_account_id': self.partner1bank1.id,
            },
            context={}
        )

        act_win = self.ScanBVR.validate_bvr_string(
            cr, uid, [wizard_id], context={})
        assert act_win['res_id']
        assert self.partner1bank1.bvr_adherent_num

        new_invoice = self.Invoice.browse(cr, uid, act_win['res_id'])
        assert float_compare(new_invoice.amount_total, 3949.75,
                             precision_rounding=0.01) == 0
