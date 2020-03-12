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
            data.update({
                'img_src': ('src', image),
                'modal_id': ('id', 'img' + str(related_file.id)),
                'data_target': ('data-target', '#img' + str(related_file.id))
            })
        return data
