# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class BusinessDocumentImport(models.AbstractModel):
    _name = "business.document.import"
    _description = "Common methods to import business documents"

    @api.model
    def _hook_match_partner(
        self, partner_dict, chatter_msg, domain, partner_type_label
    ):
        # TODO search by iban
        return False
