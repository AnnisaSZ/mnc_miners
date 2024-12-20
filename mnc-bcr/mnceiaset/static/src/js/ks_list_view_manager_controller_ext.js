odoo.define('mnceiaset.controller', function (require) {
    "use strict";

     var core = require('web.core');
    var ajax = require('web.ajax');
    var QWeb = core.qweb;
    var session = require('web.session');
    var Dialog = require('web.Dialog');
    var fieldUtils = require('web.field_utils');
    var ListController = require('web.ListController');
    var framework = require('web.framework');
    var view_registry = require('web.view_registry');
    var dom = require('web.dom');
    var ActionManager = require('web.ActionManager');
    var ListView = require('web.ListView');
    var _t = core._t;
    var inventory_validate_button = view_registry.get('inventory_validate_button');
    var basic_model = require('web.BasicModel');

    ListController.include({
        init: function (parent, model, renderer, params) {
            if(params.initialState.context.remove_ks == true){
                this._super.apply(this, arguments);
                this.ks_lvm_mode = false;
                // this._super.apply(this, arguments);
            } else {
                this._super.apply(this,arguments);
            }
        },
    });

    return ListController;
});