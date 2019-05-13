odoo.define('specific_account.esr_reconciliation', function (require) {
"use strict";

var AccountReconciliation = require('account.reconciliation');
var core = require('web.core');


// Add a second button to reconcilation widget which only reconciles based on esr.
AccountReconciliation.bankStatementReconciliation.include({
    start: function() {
        var self = this;
        return $.when(this._super()).then(function(){
                self.$el.find('.js_esr_reconciliation').click(function() {
                    self.model_bank_statement_line
                        .call("reconciliation_widget_auto_reconcile",
                            [self.lines || undefined, self.num_already_reconciled_lines],
                            {'context': {'esr_reconcile': true}}
                        )
                        .then(function(data){
                            self.serverPreprocessResultHandler(data);
                        })
                        .then(function(){
                            self.$('.js_esr_reconciliation').hide();
                            return self.display_reconciliation_propositions();
                        });

                });

            });
    },
});
});
