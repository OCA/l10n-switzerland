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
from openerp import models, api, _, fields


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    lsv_treatment_type = fields.Selection(
        [('P', _('Production')),
         ('T', _('Test')),
         ],
        string="LSV Treatment Type",
        required=True,
        default='T',
        help='Mode to use when generating an LSV payment file with this payment method.'
    )
