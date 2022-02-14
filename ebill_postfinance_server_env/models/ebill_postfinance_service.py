# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class EbillPostfinanceService(models.Model):
    _name = "ebill.postfinance.service"
    _inherit = ["ebill.postfinance.service", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        return {
            "use_test_service": {},
            "username": {},
            "password": {},
        }
