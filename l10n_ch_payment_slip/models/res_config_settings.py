# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    isr_delta_horz = fields.Float(
        related='company_id.isr_delta_horz',
    )
    isr_delta_vert = fields.Float(
        related='company_id.isr_delta_vert',
    )
    isr_scan_line_vert = fields.Float(
        related='company_id.isr_scan_line_vert',
    )
    isr_scan_line_horz = fields.Float(
        related='company_id.isr_scan_line_horz',
    )
    isr_add_vert = fields.Float(
        related='company_id.isr_add_vert',
    )
    isr_add_horz = fields.Float(
        related='company_id.isr_add_horz',
    )
    isr_scan_line_font_size = fields.Integer(
        related='company_id.isr_scan_line_font_size',
    )
    isr_scan_line_letter_spacing = fields.Float(
        related='company_id.isr_scan_line_letter_spacing',
    )
    isr_amount_line_horz = fields.Float(
        related='company_id.isr_amount_line_horz',
    )
    isr_amount_line_vert = fields.Float(
        related='company_id.isr_amount_line_vert',
    )
    merge_mode = fields.Selection(
        related='company_id.merge_mode'
    )
    isr_background = fields.Boolean(
        related='company_id.isr_background',
    )
    isr_header_partner_address = fields.Boolean(
        related='company_id.isr_header_partner_address',
    )
