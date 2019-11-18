
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields
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
            return True
        else:
            raise UserError("Parsing failed, please try with a correct file.")
