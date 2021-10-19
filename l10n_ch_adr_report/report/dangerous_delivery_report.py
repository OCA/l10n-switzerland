# Copyright 2019 Iryna Vyshnevska (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from itertools import groupby

from odoo import models


class DangerousDeliverCHADR(models.AbstractModel):
    _name = "report.l10n_ch_adr_report.report_dg_l10n_ch"
    _description = "Dangerous Delivery Report ADR"

    def _get_report_values(self, docids, data=None):
        docs = self.env["stock.picking"]
        data = data or {}
        docs = self.env["stock.picking"].browse(docids)
        dg_data = self.prepare_DG_data(docs)
        docargs = {
            "doc_ids": docs.ids,
            "doc_model": "stock.picking",
            "docs": docs,
            "data": data.get("form", False),
            "DG_data": dg_data,
        }
        return docargs

    def prepare_DG_data(self, picking_ids):
        """
        Result is lines for dangerous products
        :return: dict
        {'dg_lines':[{
                'product': product.product(40,),
                'class': 'UN UN Number, ...
                'packaging_type': adr_packing_instruction_ids(6,),
                'qty_amount': 100.0,
                'product_weight': 10.0,
                'column_index': '3',
                'dangerous_amount': 1000.0
            }],
        'total_section':{
            'total_units': {'1': 0, '2': 0, '3': 1000.0, '4': 0, '5': 0},
            'factor': {'1': 0.0, '2': 50.0, '3': 3.0, '4': 1.0, '5': 0.0},
            'mass_points': {'1': 0.0, '2': 0.0, '3': 3000.0, '4': 0.0, '5': 0.0},
            'total_points': 3000.0,
            'warn': True
            }
        }
        """

        vals = {
            "dg_lines": [],
            "total_section": {},
        }
        for pick in picking_ids:
            if pick.state == "done":
                moves = pick.move_lines.filtered(lambda l: l.state == "done")
            else:
                moves = pick.move_lines
            dangerous_moves = moves.filtered(lambda self: self.product_id.is_dangerous)
            grouped_moves = groupby(
                sorted(dangerous_moves, key=lambda l: l.product_id),
                lambda r: r.product_id,
            )
            vals["dg_lines"] += self._get_DG_move_line_vals(grouped_moves)

        vals["total_section"] = self._compute_points_per_product(vals["dg_lines"])
        vals["total_section"]["total_points"] = self._compute_total_points(
            vals["total_section"]
        )
        vals["total_section"]["warn"] = self._is_limit_exceeded(vals["total_section"])
        return vals

    def _compute_points_per_product(self, vals):
        index = {}.fromkeys(["1", "2", "3", "4", "5"], 0.0)
        total_vals = {
            "total_units": index.copy(),
            "factor": index.copy(),
            "mass_points": index.copy(),
            "total_points": 0.0,
        }
        self._init_total_vals(total_vals)

        for k in index.keys():
            total_vals["total_units"][k] = self._sum_values(vals, "dangerous_amount", k)
            total_vals["mass_points"][k] = self._apply_rounding(
                total_vals["total_units"][k] * total_vals["factor"][k]
            )
        return total_vals

    def _sum_values(self, vals, field, index):
        return sum([item[field] for item in vals if item["column_index"] == index])

    def _compute_total_points(self, vals):
        return self._apply_rounding(sum(vals["mass_points"].values()))

    def _apply_rounding(self, amount):
        # should follow precision on product
        return round(amount, 1)

    def _is_limit_exceeded(self, vals):
        if vals["total_points"] > 1000.0:
            return True
        return False

    def _init_total_vals(self, vals):
        vals["factor"]["1"] = 0.0
        vals["factor"]["2"] = 50.0
        vals["factor"]["3"] = 3.0
        vals["factor"]["4"] = 1.0
        vals["factor"]["5"] = 0.0

    def _get_DG_move_line_vals(self, moves):
        # unit measurement on stock is not considered
        result = []
        for product, move_lines in moves:
            qty = 0
            for rec in move_lines:
                if rec.state == "done":
                    qty += rec.quantity_done
                else:
                    qty += rec.product_uom_qty
            result.append(
                {
                    "product": product,
                    "class": product.adr_goods_id.name,
                    "packaging_type": product.adr_packing_instruction_ids.mapped(
                        "code"
                    ),
                    "qty_amount": qty,
                    "product_weight": product.weight,
                    "column_index": str(product.adr_transport_category),
                    "dangerous_amount": qty * product.weight,
                }
            )

        return result
