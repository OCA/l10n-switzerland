# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # allow related to edit as it only view where its possible to do
    isr_delta_horz = fields.Float(
        related='company_id.isr_delta_horz',
        readonly=False,
    )
    isr_delta_vert = fields.Float(
        related='company_id.isr_delta_vert',
        readonly=False,
    )
    isr_scan_line_vert = fields.Float(
        related='company_id.isr_scan_line_vert',
        readonly=False,
    )
    isr_scan_line_horz = fields.Float(
        related='company_id.isr_scan_line_horz',
        readonly=False,
    )
    isr_add_vert = fields.Float(
        related='company_id.isr_add_vert',
        readonly=False,
    )
    isr_add_horz = fields.Float(
        related='company_id.isr_add_horz',
        readonly=False,
    )
    isr_scan_line_font_size = fields.Integer(
        related='company_id.isr_scan_line_font_size',
        readonly=False,
    )
    isr_scan_line_letter_spacing = fields.Float(
        related='company_id.isr_scan_line_letter_spacing',
        readonly=False,
    )
    isr_amount_line_horz = fields.Float(
        related='company_id.isr_amount_line_horz',
        readonly=False,
    )
    isr_amount_line_vert = fields.Float(
        related='company_id.isr_amount_line_vert',
        readonly=False,
    )
    merge_mode = fields.Selection(
        related='company_id.merge_mode',
        readonly=False,
    )
    isr_background = fields.Boolean(
        related='company_id.isr_background',
        readonly=False,
    )
    isr_header_partner_address = fields.Boolean(
        related='company_id.isr_header_partner_address',
        readonly=False,
    )
