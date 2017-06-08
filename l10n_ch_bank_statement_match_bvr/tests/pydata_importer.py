# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models
import ast


class AccountBankStatementImport(models.TransientModel):
    """Mock importer that just pulls raw python objects out a data file."""
    _name = 'l10n_ch_bank_statement_match_bvr.tests.pydata_importer'
    _inherit = 'account.bank.statement.import'

    @api.model
    def _parse_file(self, data_file):
        return ast.literal_eval(data_file)
