odoo.define('mnc_fuel_management.controller', function (require) {
"use strict";

var rpc = require('web.rpc');
var ListController = require('ks_list_view_manager.controller');
var BasicView = require('web.BasicView');


ListController.include({
        ks_reload_list_view: function(viewInfo, params) {
            var data = this._super.apply(this, arguments);
            if (this.modelName == 'fuel.distribution.line') {
                rpc.query({
                    model: this.modelName,
                    method: 'search',
                    args: [[]],
                })
                .then(function (line_ids) {
                    for (let i = 0; i < line_ids.length; i++) {
                        console.log(line_ids[i]);
                        rpc.query({
                            model: 'fuel.distribution.line',
                            method: 'action_update_data',
                            args: [line_ids[i]],
                        })
                    }
                });
            }

            return data;
        },
    });
});