odoo.define('l10n_ch_payment_slip.report', function(require){
'use strict';

var ActionManager= require('web.ActionManager');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');


ActionManager.include({
    ir_actions_report: function (action, options){
        if (action.report_type === 'reportlab_pdf') {
            var client_action_options = _.extend({}, options, {
                report_url: '/report/reportlab_pdf/' + action.report_name + '/' + action.context.active_ids.join(','),
                report_name: action.report_name,
                report_file: action.report_file,
                data: action.data,
                context: action.context,
                name: action.name,
                display_name: action.display_name,
            });
            this.getSession().get_file({
                url: client_action_options.report_url,
                data: {data: JSON.stringify([
                    client_action_options.report_url,
                    action.report_type,
                ])},
                error: crash_manager.rpc_error.bind(crash_manager),
                success: function() {
                    if(action && options && !action.dialog){
                        options.on_close();
                    }
                },
            });
            framework.unblockUI()
            return
        }
        return this._super(action, options)
    }
});
});
