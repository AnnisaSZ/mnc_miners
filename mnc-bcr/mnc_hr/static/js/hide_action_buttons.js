odoo.define('mnc_hr.BasicView', function (require) {
"use strict";
var BasicView = require('web.BasicView');
BasicView.include({

        init: function(viewInfo, params) {
            var self = this;
            this._super.apply(this, arguments);
            const model =  ['mncei.employee'];
            if(model.includes(self.controllerParams.modelName))
            {
               self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
            }
        },
    });
});