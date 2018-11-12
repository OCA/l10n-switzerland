# -*- coding: utf-8 -*-
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields
import os
import inspect
import base64

import logging
_logger = logging.getLogger(__name__)


class HRImpSource(models.Model):
    _name = 'hr.imp.src'

    imp_src_barem = fields.Char(string="Barem")
    rate = fields.Float(string="Taux (%)")
    range_from = fields.Float(string="Salaire depuis")
    range_to = fields.Float(string="Salaire à")
    is_eccle = fields.Boolean(string="Soumis à l'impot ecclésiastique ?")
    canton = fields.Char(string="Canton")


class HRImpSourceImport(models.TransientModel):
    _name = 'hr.imp.src.import'

    rate_file = fields.Binary(string="Fichiers de barème")
    
    def import_rates(self):
        self.ensure_one()
        new_lines = []
        for line in base64.b64decode(self.rate_file).splitlines():
            line_parsed = {}
            record_type = line[0:2]
            if record_type == b'06':
                line_parsed = {
                    'canton': line[4:6],
                    'imp_src_barem': line[6:8],
                    'is_eccle': True if line[8:9] == b'Y' else False,
                    'rate': int(line[55:57]) + int(line[57:59]) / 100.0,
                    'range_from': int(line[24:31]) + int(line[31:33])/100.0,
                    'range_to': (int(line[24:31]) + int(line[31:33])/100.0) + int(line[33:40])
                }
                new_line = self.env['hr.imp.src'].create(line_parsed)
                new_lines.append(new_line.id)
        [action] = self.env.ref('l10n_ch_hr_payroll.action_imp_src').read()
        action.update({'domain': [('id', 'in', new_lines)]})
        return action
