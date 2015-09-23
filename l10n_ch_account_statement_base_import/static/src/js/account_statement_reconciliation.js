/* This is Javascript extension of module account
   in order to add custom reconcile buttons in the 
   Manual Reconcile view */
openerp.l10n_ch_account_statement_base_import = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    

    // Extend the class written in module account (bank statement view)
    instance.web.account.bankStatementReconciliationLine.include({

        decorateStatementLine: function(line){
            this._super(line);
            line.i_popover = QWeb.render("bank_statement_reconciliation_line_image", {line: line});
        },

    });
};
