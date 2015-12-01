# -*- coding: utf-8 -*-
#
#  File: models/account_move_line.py
#  Module: l10n_ch_hr_payroll
#
#  Created by cyp@open-net.ch
#
#  Copyright (c) 2015-TODAY Open-Net Ltd.
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # ---------- Fields management

    slip_id = fields.Many2one('hr.payslip', string='Pay slip')

    # ---------- Instances management

    @api.model
    def create(self, vals):
        new_rec = super(AccountMoveLine, self).create(vals)

        # This is for the cases when the first account_move_line
        # doesn't have a partner_id but the others have one.
        if new_rec.account_id.type == 'payable' and new_rec.partner_id:
            query = """update account_move
set partner_id=%d
where id=%d""" % (new_rec.partner_id.id, new_rec.move_id.id)
            self._cr.execute(query)

        return new_rec

    def write(self, cr, uid, ids, vals, context=None,
              check=True, update_check=True):

        _super = super(AccountMoveLine, self)
        ret = _super.write(
            cr, uid, ids, vals, context=context,
            check=check, update_check=update_check
        )

        # This is for the cases when the first account_move_line
        # doesn't have a partner_id but the others have one.
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.account_id.type != 'payable' or not rec.partner_id:
                continue
            query = """update account_move
set partner_id=%d
where id=%d""" % (rec.partner_id.id, rec.move_id.id)
            cr.execute(query)

        return ret
