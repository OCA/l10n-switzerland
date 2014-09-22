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

from openerp.osv import orm


class DTAFileGenerator(orm.TransientModel):
    _inherit = "create.dta.wizard"

    def _set_bank_data(self, cr, uid, data, pline, elec_context,
                       seq, context=None):
        super(DTAFileGenerator, self).\
            _set_bank_data(cr, uid, data, pline,
                           elec_context, seq, context=context)
        if pline.move_line_id.transaction_ref:
            elec_context['reference'] = pline.move_line_id.transaction_ref
