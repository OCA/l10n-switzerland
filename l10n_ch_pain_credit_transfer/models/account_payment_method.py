# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    pain_version = fields.Selection(selection_add=[
        ('pain.001.001.03.ch.02',
         'pain.001.001.03.ch.02 (credit transfer in Switzerland)'),
        ])

    @api.multi
    def get_xsd_file_path(self):
        self.ensure_one()
        painv = self.pain_version
        if painv == 'pain.001.001.03.ch.02':
            path = 'l10n_ch_pain_credit_transfer/data/%s.xsd' % painv
            return path
        return super(AccountPaymentMethod, self).get_xsd_file_path()
