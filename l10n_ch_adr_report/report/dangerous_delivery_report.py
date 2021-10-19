# Copyright 2019 Iryna Vyshnevska (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class DangerousDeliverCHADR(models.AbstractModel):
    _name = "report.l10n_ch_adr_report.report_dg_l10n_ch"
    _description = "Dangerous Delivery Report ADR"

    def _get_report_values(self, docids, data=None):
        docs = self.env["stock.picking"]
        data = data or {}
        docs = self.env["stock.picking"].browse(docids)
        wizard = self.env["dangerous.goods.handler"].create(
            {"picking_ids": [(6, 0, docs.ids)]}
        )
        dg_data = wizard.prepare_DG_data()
        docargs = {
            "doc_ids": docs.ids,
            "doc_model": "stock.picking",
            "docs": docs,
            "data": data.get("form", False),
            "DG_data": dg_data,
        }
        return docargs
