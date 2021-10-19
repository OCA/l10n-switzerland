# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PaynetService(models.Model):
    _name = "paynet.service"
    _inherit = ["paynet.service", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        return {
            "use_test_service": {},
            "username": {},
            "password": {},
        }
