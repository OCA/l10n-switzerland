# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def generate_email(self, res_ids, fields=None):
        # This uses https://github.com/odoo/odoo/pull/79318
        self = self.with_context(
            l10n_ch_mail_skip_report=(
                "l10n_ch.l10n_ch_isr_report",
                "l10n_ch.l10n_ch_qr_report",
            )
        )
        return super(MailTemplate, self).generate_email(res_ids, fields)
