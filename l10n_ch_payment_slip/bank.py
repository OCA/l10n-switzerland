# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
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
from openerp import models, fields, api


class ResPartnerBank(models.Model):
    """
    Inherit res.partner.bank class in order to add swiss specific fields
    such as:
     - BVR data
     - BVR print options for company accounts
     We leave it here in order
    """
    _inherit = "res.partner.bank"

    print_bank = fields.Boolean('Print Bank on BVR')
    print_account = fields.Boolean('Print Account Number on BVR')
    print_partner = fields.Boolean('Print Partner Address on BVR')

    @api.multi
    def _display_address(self):
        """ Format bank address """
        self.ensure_one()
        address_format = (
            self.country_id.address_format or
            "%(company_name)s\n%(street)s\n%(city)s %(state_code)s"
            " %(zip)s\n%(country_name)s")
        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',
            'company_name': self.owner_name or '',
            'street2': '',  # No such field on the this model
        }
        for field in ('street', 'zip', 'city', 'state_id', 'country_id'):
            args[field] = getattr(self, field) or ''
        return address_format % args
