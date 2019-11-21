# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    pain_version = fields.Selection(selection_add=[
        ('pain.008.001.02.ch.03',
         'pain.008.001.02.ch.03 (XML Direct Debit)'),
        ])

    @api.multi
    def get_xsd_file_path(self):
        self.ensure_one()
        pain_version = self.pain_version
        if pain_version == 'pain.008.001.02.ch.03':
            path = 'l10n_ch_pain_direct_debit/data/%s.xsd' % pain_version
            return path
        return super(AccountPaymentMethod, self).get_xsd_file_path()
