odoo.define('l10n_ch_account_reconcile_isr.isr_reconciliation', function (require) {
"use strict";

var AccountReconciliation = require('account.reconciliation');
var core = require('web.core');


// Add a second button to reconcilation widget which only reconciles based on ISR.
AccountReconciliation.bankStatementReconciliation.include({
    start: function() {
        var self = this;
        return $.when(this._super()).then(function(){
                self.$el.find('.js_isr_reconciliation').click(function() {
                    self.model_bank_statement_line
                        .call("reconciliation_widget_auto_reconcile",
                            [self.lines || undefined, self.num_already_reconciled_lines],
                            {'context': {'isr_reconcile': true}}
                        )
                        .then(function(data){
                            self.serverPreprocessResultHandler(data);
                        })
                        .then(function(){
                            self.$('.js_isr_reconciliation').hide();
                            return self.display_reconciliation_propositions();
                        });

                });

            });
    },
});
});
