/* Copyright 2014-2017 Compassion CH
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */
odoo.define('l10n_ch_bank_statement_import_postfinance.reconciliation', function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var reconciliation = require('account.reconciliation');

    // Extend the class written in module account (bank statement view)
    reconciliation.bankStatementReconciliationLine.include({
        decorateStatementLine: function(line){
            this._super(line);
            line.i_popover = QWeb.render("bank_statement_reconciliation_line_image", {line: line});
        },
    });
});
