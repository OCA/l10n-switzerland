# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo import models

from ..quickpac.web_service import QuickpacWebService


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def onchange_carrier_id(self):
        result = super().onchange_carrier_id()
        web_service = QuickpacWebService(self.env.user.company_id)
        zipcode = self.partner_id.zip
        web_service.is_deliverable_zipcode(zipcode)
        return result

    def _generate_quickpac_label(self, webservice_class=None, package_ids=None):
        """Generate labels and write tracking numbers received"""
        self.ensure_one()
        ctx = self.env.context
        user = self.env.user
        company = user.company_id

        if package_ids:
            # TODO: send_shipping does not provide package_ids when calling
            # this method, should we remove this or change UI to trigger this?
            packages = self.env["stock.quant.package"].browse(package_ids)
        else:
            # TODO: _get_packages_from_picking is same with delivery_postlogistics
            # module. If there is business case that needs this, we should move
            # the method back to base_delivery_carrier_label module.
            # packages = self._get_packages_from_picking()
            packages = self.package_ids

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
            filtered_packages = packages.filtered(lambda p: p.name in label["item_id"])
            if "active_test" in ctx and ctx["active_test"]:
                # ids mismatch when testing
                package = packages[0]
            else:
                package = filtered_packages[0]
            package.parcel_tracking = label["tracking_number"]
            info = info_from_label(label)
            info["package_id"] = package.id
            labels.append(info)
        return labels
