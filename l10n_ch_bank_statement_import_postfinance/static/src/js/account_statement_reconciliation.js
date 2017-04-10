/* This is Javascript extension of module account
   in order to add custom reconcile buttons in the 
   Manual Reconcile view */
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
