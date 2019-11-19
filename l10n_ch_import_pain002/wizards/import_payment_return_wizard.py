
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields, _
import base64

from odoo.exceptions import UserError


class PaymentReturnWizard(models.TransientModel):
    _name = 'import.payment.return.wizard'
    _description = 'Import payment return file'

    file = fields.Binary()

    @api.multi
    def import_payment_return_file(self):
        self.ensure_one()
        data = str(base64.decodebytes(self.file), 'utf-8')
        parsed, parsed_obj = self.env['account.pain002.parser'].parse(data)

        if parsed:
            if parsed_obj:
                return {
                    'name': 'Payment Order Form View',
                    'view_mode': 'form,tree',
                    'res_model': parsed_obj._name,
                    'res_id': parsed_obj.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                }
            else:
                raise UserError(_("No related payment order found."))
        else:
            raise UserError(_("Parsing failed, please try with a correct file."))
