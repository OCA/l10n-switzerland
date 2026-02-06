# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute(
        """
        UPDATE account_payment_method SET pain_version = 'pain.001.001.09.ch.03'
        WHERE pain_version = 'pain.001.001.03.ch.02'
        AND code = 'sepa_credit_transfer'
        AND payment_type = 'outbound'
        """
    )
