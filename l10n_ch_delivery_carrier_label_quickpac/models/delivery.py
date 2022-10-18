# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..quickpac.helpers import get_language

QUICKPAC_TYPES = [
    ("label_layout", "Label Layout"),
    ("output_format", "Output Format"),
    ("resolution", "Output Resolution"),
    ("basic", "Basic Service"),
    ("additional", "Additional Service"),
    ("delivery", "Delivery Instructions"),
]
SINGLE_OPTION_TYPES = ["label_layout", "output_format", "resolution"]


class DeliveryCarrierTemplateOption(models.Model):
    """Set name translatable and add service group"""

    _inherit = "delivery.carrier.template.option"

    name = fields.Char(translate=True)
    quickpac_type = fields.Selection(
        selection=QUICKPAC_TYPES, string="Quickpac option type"
    )


class DeliveryCarrierOption(models.Model):
    """Set name translatable and add service group"""

    _inherit = "delivery.carrier.option"

    name = fields.Char(related="tmpl_option_id.name")

    allowed_tmpl_options_ids = fields.Many2many(
        "delivery.carrier.template.option",
        compute="_compute_allowed_tmpl_options_ids",
        store=False,
    )

    @api.depends("carrier_id.allowed_tmpl_options_ids")
    def _compute_allowed_tmpl_options_ids(self):
        """Gets the available template options from related delivery.carrier
        (be it from cache or context)."""
        for option in self:
            defaults = self.env.context.get("default_allowed_tmpl_options_ids")
            option.allowed_tmpl_options_ids = (
                option.carrier_id.allowed_tmpl_options_ids or defaults or False
            )


class DeliveryCarrier(models.Model):
    """Add service group"""

    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("quickpac", "Quickpac")],
        ondelete={"quickpac": "set default"},
    )
    allowed_tmpl_options_ids = fields.Many2many(
        "delivery.carrier.template.option",
        compute="_compute_allowed_options_ids",
    )

    @api.depends(
        "delivery_type",
        "available_option_ids",
        "available_option_ids.quickpac_type",
    )
    def _compute_allowed_options_ids(self):
        """Compute allowed delivery.carrier.option.

        We do this to ensure the user first select a basic service. And
        then he adds additional services.
        """
        option_template_obj = self.env["delivery.carrier.template.option"]

        for carrier in self:
            forbidden = option_template_obj.browse()
            domain = []
            qp_xmlid = "l10n_ch_delivery_carrier_label_quickpac.partner_quickpac"
            if carrier.delivery_type != "quickpac":
                domain.append(("partner_id", "!=", self.env.ref(qp_xmlid).id)),
            else:
                # Allows to set multiple optional single option in order to
                # let the user select them
                selected_single_options = [
                    opt.tmpl_option_id.quickpac_type
                    for opt in carrier.available_option_ids
                    if opt.quickpac_type in SINGLE_OPTION_TYPES and opt.mandatory
                ]
                if selected_single_options != SINGLE_OPTION_TYPES:
                    services = option_template_obj.search(
                        [
                            ("quickpac_type", "in", SINGLE_OPTION_TYPES),
                            ("quickpac_type", "in", selected_single_options),
                        ]
                    )
                    forbidden |= services
                domain.append(("partner_id", "=", self.env.ref(qp_xmlid).id)),
                domain.append(("id", "not in", forbidden.ids))

            carrier.allowed_tmpl_options_ids = option_template_obj.search(domain)

    def quickpac_send_shipping(self, pickings):
        """
        This will generate the labels for all the packages of the picking.
        """
        res = []
        for pick in pickings:
            labels = pick._generate_quickpac_label()
            res.append(
                {
                    "labels": labels,
                    "exact_price": False,
                    "tracking_number": labels[0]["tracking_number"],
                }
            )

        return res

    @api.model
    def quickpac_get_tracking_link(self, picking):
        tracking_url = picking.company_id.quickpac_tracking_url
        return tracking_url.format(
            lang=get_language(picking.partner_id.lang),
            number=picking.carrier_tracking_ref,
        )

    def quickpac_cancel_shipment(self, pickings):
        raise NotImplementedError()
