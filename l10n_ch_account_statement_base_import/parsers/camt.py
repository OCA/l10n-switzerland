# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.addons.account_bank_statement_import_camt.camt import CamtParser


class PFCamtParser(CamtParser):
    """Parser for camt bank statement files of PostFinance SA."""

    def parse_transaction_details(self, ns, node, transaction):
        """Change how reference is read."""
        # eref
        self.add_value_from_node(
            ns, node, './ns:Refs/ns:AcctSvcrRef', transaction, 'eref')
        super(PFCamtParser, self).parse_transaction_details(
            ns, node, transaction)
