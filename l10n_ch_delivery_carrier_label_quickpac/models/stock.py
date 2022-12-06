# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo import api, models

from ..quickpac.web_service import QuickpacWebService


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _generate_quickpac_label(self, webservice_class=None, package_ids=None):
        """ Generate labels and write tracking numbers received """
        self.ensure_one()
        ctx = self.env.context
        user = self.env.user
        company = user.company_id

        if package_ids:
            packages = self.env['stock.quant.package'].browse(package_ids)
        else:
            packages = self._get_packages_from_picking()

        if webservice_class:
            web_service = webservice_class(company)
        else:
            web_service = QuickpacWebService(company)
        res = web_service.generate_label(self, packages)

        def info_from_label(label):
            tracking_number = label["tracking_number"]
            return {
                "file": base64.b64decode(label["binary"]),
                "file_type": label["file_type"],
                "name": tracking_number + "." + label["file_type"],
                "tracking_number": tracking_number,
            }

        labels = []
        for item in res:
            label = item["value"]
            filtered_packages = packages.filtered(
                lambda p: p.name in label['item_id']
            )
            if "active_test" in ctx and ctx["active_test"]:
                # ids mismatch when testing
                package = packages[0]
            else:
                package = filtered_packages[0]
            package.parcel_tracking = label['tracking_number']
            info = info_from_label(label)
            info['package_id'] = package.id
            labels.append(info)
        return labels

    @api.multi
    def generate_shipping_labels(self):
        """ Add label generation for Quickpac"""
        self.ensure_one()
        delivery_type = self.carrier_id.delivery_type
        if delivery_type == "quickpac":
            return self._generate_quickpac_label()
        return super().generate_shipping_labels()
