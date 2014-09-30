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
from openerp.osv import orm, fields
from openerp.tools import mod10r
from openerp.tools.translate import _


class res_partner_bank(orm.Model):

    ''' Inherit res.partner.bank class in order to add swiss specific
    fields such as:
     - LSV identifier
     - Bank BVR customer Number (ESR party number)
     - Postfinance Direct Debit identifier
    '''
    _inherit = "res.partner.bank"
    _columns = {
        'lsv_identifier': fields.char(
            _('LSV Identifier'), size=5, help=_(
                "Enter the LSV Identifier that has been attributed "
                "to your company to make LSV Direct Debits. This identifier "
                "is composed of 5 alphanumeric characters and is required "
                "to generate LSV direct debit orders.")),
        'post_dd_identifier': fields.char(
            _('Postfinance DD Customer No.'), size=6),
        'esr_party_number': fields.char(
            _('ESR party number'), size=9, help=_(
                "ESR party number is an identifier attributed to your "
                "bank to generate ESR references. This identifier is "
                "composed of up to 9 alphanumeric characters and is "
                "required when using ESR references in your LSV direct "
                "debit orders")),
    }

    ################################
    #          Constraints         #
    ################################

    def _check_lsv_identifier(self, cr, uid, ids):
        for bank_account in self.browse(cr, uid, ids):
            # Check is only done if field is not empty
            if bank_account.lsv_identifier:
                if not self.is_lsv_identifier_valid(
                        cr, uid, bank_account.lsv_identifier):
                    return False
        return True

    def _check_post_dd_identifier(self, cr, uid, ids):
        for bank_account in self.browse(cr, uid, ids):
            # Check is only done if field is not empty
            if bank_account.post_dd_identifier:
                if not self.is_post_dd_ident_valid(
                        cr, uid, bank_account.post_dd_identifier):
                    return False
        return True

    _constraints = [
        (_check_lsv_identifier, _("Invalid LSV Identifier."),
            ['lsv_identifier']),
        (_check_post_dd_identifier, _("Invalid Postfiance DD Identifier."),
            ['post_dd_identifier']),
    ]

    def is_lsv_identifier_valid(self, cr, uid, lsv_identifier, context=None):
        """ Check if given LSV Identifier is valid """
        if not isinstance(lsv_identifier, basestring):
            return False
        try:
            lsv_identifier.decode('ascii')
        except UnicodeDecodeError:
            raise orm.except_orm('ValidateError',
                                 _('LSV identifier should contain only ASCII'
                                   'caracters.'))

        if not len(lsv_identifier) == 5:
            return False

        return True

    def is_post_dd_ident_valid(self, cr, uid, dd_identifier, context=None):
        """ Check if given Postfinance DD Identifier is valid """
        if not isinstance(dd_identifier, basestring):
            return False
        try:
            dd_identifier.decode('ascii')
        except UnicodeDecodeError:
            raise orm.except_orm('ValidateError',
                                 _('DD identifier should contain only ASCII '
                                   'caracters.'))

        if not len(dd_identifier) == 6:
            return False

        if not dd_identifier == mod10r(dd_identifier[:5]):
            return False

        return True
