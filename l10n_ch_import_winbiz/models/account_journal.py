# -*- coding: utf-8 -*-
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    winbiz_mapping = fields.Char(string='WinBIZ journal code')
