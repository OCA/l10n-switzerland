# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
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

"""
The banks have been created on the l10n_ch module because they used
the wrong namespace (ie ``l10_ch.bank_0``). Now, the records are created
in the correct module but we have to correct the existing records.
"""


def migrate(cr, version):
    if not version:
        return

    query = ("UPDATE ir_model_data "
             "SET module = 'l10n_ch_bank' "
             "WHERE module = 'l10n_ch' "
             "AND model = 'res.bank' ")
    cr.execute(query)
