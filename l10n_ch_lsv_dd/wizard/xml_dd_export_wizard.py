##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2017 brain-tec AG (http://www.braintec-group.com)
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

from openerp import models, fields, api, _, exceptions

import logging
logger = logging.getLogger(__name__)


class XmlDdExportWizard(models.TransientModel):
    """ XML Direct Debit file generation wizard.
    """
    _name = 'xml.dd.export.wizard'
    _description = 'XML Postfinance Direct Debit File'

    currency = fields.Selection(
        [('CHF', 'CHF'),
         ('EUR', 'EUR'),
         ('USD', 'USD'),
         ],
        required=True,
        default='CHF'
    )

    @api.multi
    def generate_xml_dd_file(self):
        """ Generates the XML Direct Debit file. This method is called from the wizard.
        """
        self.ensure_one()
        payment_order_obj = self.env['account.payment.order']

        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise exceptions.ValidationError(_('No payment order selected'))

        payment_orders = payment_order_obj.browse(active_ids)
        for payment_order in payment_orders:
            payment_order.generate_xml_ch_dd_file()

        action = {
            'name': _('Generated File'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',
        }
        return action
