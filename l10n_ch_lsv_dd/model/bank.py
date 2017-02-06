##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2014 Compassion (http://www.compassion.ch)
#    @author: Cyril Sester <cyril.sester@outlook.com>
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
from openerp.tools import mod10r


class ResPartnerBank(models.Model):

    ''' Inherit res.partner.bank class in order to add swiss specific
    fields such as:
     - LSV identifier
     - Bank BVR customer Number (ESR party number)
     - Postfinance Direct Debit identifier
    '''
    _inherit = "res.partner.bank"

    lsv_identifier = fields.Char(
        'LSV Identifier',
        size=5,
        help="Enter the LSV Identifier that has been attributed "
             "to your company to make LSV Direct Debits. This identifier "
             "is composed of 5 alphanumeric characters and is required "
             "to generate LSV direct debit orders."
    )
    post_dd_identifier = fields.Char(
        'Postfinance DD Customer No.',
        size=6
    )
    esr_party_number = fields.Char(
        'ESR party number',
        size=9,
        help="ESR party number is an identifier attributed to your "
             "bank to generate ESR references. This identifier is "
             "composed of up to 9 alphanumeric characters and is "
             "required when using ESR references in your LSV direct "
             "debit orders"
    )

    ################################
    #          Constraints         #
    ################################

    @api.constrains('lsv_identifier')
    def _check_lsv_identifier(self):
        for bank_account in self:
            # Check is only done if field is not empty
            if bank_account.lsv_identifier:
                if not self.is_lsv_identifier_valid(bank_account
                                                    .lsv_identifier):
                    raise exceptions.ValidationError(
                        _("Invalid LSV Identifier.")
                    )
        return True

    @api.constrains('post_dd_identifier')
    def _check_post_dd_identifier(self):
        for bank_account in self:
            # Check is only done if field is not empty
            if bank_account.post_dd_identifier:
                if not self.is_post_dd_ident_valid(bank_account
                                                   .post_dd_identifier):
                    raise exceptions.ValidationError(_("Invalid Postfiance DD"
                                                       "Identifier."))
        return True

    @api.model
    def is_lsv_identifier_valid(self, lsv_identifier):
        """ Check if given LSV Identifier is valid """
        if not isinstance(lsv_identifier, basestring):
            return False
        try:
            lsv_identifier.decode('ascii')
        except UnicodeDecodeError:
            raise exceptions.ValidationError(
                _('LSV identifier should contain only ASCII caracters.')
            )

        if not len(lsv_identifier) == 5:
            return False

        return True

    @api.model
    def is_post_dd_ident_valid(self, dd_identifier):
        """ Check if given Postfinance DD Identifier is valid """
        if not isinstance(dd_identifier, basestring):
            return False
        try:
            dd_identifier.decode('ascii')
        except UnicodeDecodeError:
            raise exceptions.ValidationError(
                _('DD identifier should contain only ASCII caracters.')
            )

        if not len(dd_identifier) == 6:
            return False

        if not dd_identifier == mod10r(dd_identifier[:5]):
            return False

        return True
