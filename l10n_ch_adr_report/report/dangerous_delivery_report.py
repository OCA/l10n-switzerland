# Copyright 2019 Iryna Vyshnevska (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from itertools import groupby

from odoo import models


class DangerousDeliverCHADR(models.AbstractModel):
    _name = "report.l10n_ch_adr_report.report_dg_l10n_ch"
    _description = "Dangerous Delivery Report ADR"

    def _get_report_values(self, docids, data=None):
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
            'total_units': {'0': 0, '1': 0, '2': 1000.0, '3': 0, '4': 0},
            'factor': {'0': 0.0, '1': 50.0, '2': 3.0, '3': 1.0, '4': 0.0},
            'mass_points': {'0': 0.0, '1': 0.0, '2': 3000.0, '3': 0.0, '4': 0.0},
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
                moves = pick.move_ids.filtered(lambda m: m.state == "done")
            else:
                moves = pick.move_ids
            dangerous_moves = self._filter_dangerous_move(moves)
            grouped_moves = groupby(
                sorted(dangerous_moves, key=lambda m: m.product_id),
                lambda r: r.product_id,
            )
            vals["dg_lines"] += self._get_DG_move_line_vals(grouped_moves)

        vals["total_section"] = self._compute_points_per_product(vals["dg_lines"])
        vals["total_section"]["total_points"] = self._compute_total_points(
            vals["total_section"]
        )
        vals["total_section"]["warn"] = self._is_limit_exceeded(vals["total_section"])
        return vals

    def _filter_dangerous_move(self, moves):
        """Filter the moves to use for the report."""
        return moves.filtered(lambda move: move.product_id.is_dangerous)

    def _compute_points_per_product(self, vals):
        index = {}.fromkeys(["0", "1", "2", "3", "4"], 0.0)
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
        return vals["total_points"] > 1000.0

    def _init_total_vals(self, vals):
        vals["factor"]["0"] = 0.0
        vals["factor"]["1"] = 50.0
        vals["factor"]["2"] = 3.0
        vals["factor"]["3"] = 1.0
        vals["factor"]["4"] = 0.0

    def _get_DG_move_line_vals(self, moves):
        # unit measurement on stock is not considered
        result = []
        for product, move_lines in moves:
            qty = sum(line.quantity for line in move_lines)
            full_class_name = product.adr_report_class_display_name + (
                f", {qty}, {product.packaging_type_id.name},"
                f" {qty * product.content_package}, {product.dg_unit.name}"
            )
            result.append(
                {
                    "product": product,
                    "class": full_class_name,
                    "packaging_type": product.packaging_type_id,
                    "qty_amount": qty,
                    "product_weight": product.content_package,
                    "column_index": str(product.adr_transport_category),
                    "dangerous_amount": qty * product.content_package,
                }
            )

        return result
