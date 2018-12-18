# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from lxml import etree


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def finalize_sepa_file_creation(self, xml_root, gen_args):
        allpmtid = xml_root.findall('.//PmtId')
        for pmt in allpmtid:
            if not pmt.find('InstrId'):
                value = pmt.find('EndToEndId').text
                # Create a node, it's a copy of EndToEndId. Required for ZKB
                instruction_identification = etree.Element(
                    'InstrId')
                instruction_identification.text = value
                # Insert it at first position of PmtId node
                pmt.insert(0, instruction_identification)
        return super().finalize_sepa_file_creation(xml_root, gen_args)
