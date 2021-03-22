# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openerp import api, models


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def _hook_match_partner(
        self, partner_dict, chatter_msg, domain, partner_type_label
    ):
        # TODO search by iban
        return False
