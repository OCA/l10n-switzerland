from odoo import models, api


class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def _get_statement_line(self, st_line):
        """ Returns the data required by the bank statement reconciliation widget to
        display a statement line """

        data = super()._get_statement_line(st_line)
        if st_line.related_file.datas:
            related_file = st_line.related_file
            image = "data:image/png;base64," + related_file.datas.decode("utf-8")
            data['img_src'] = ('src', image)
        return data
