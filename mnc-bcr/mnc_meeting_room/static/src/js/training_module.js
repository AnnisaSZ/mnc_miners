// odoo.define('training_module.training_form', function (require) {
//     "use strict";

//     var FormController = require('web.FormController');
//     var Dialog = require('web.Dialog');

//     FormController.include({
//         /**
//          * This function is triggered when the 'end_date' field changes.
//          * It checks if the 'end_date' is earlier than the 'start_date',
//          * and if it is, displays an error message.
//          *
//          * @override
//          * @param {Object} record - The record being modified
//          * @param {string} fieldName - The name of the field being modified ('end_date' in this case)
//          */
//         onFieldChanged: function (record, fieldName) {
//             this._super.apply(this, arguments);
//             if (fieldName === 'end_date' && record.data.start_date && record.data.end_date < record.data.start_date) {
//                 this._showDateErrorMessage();
//             }
//         },

//         /**
//          * This function displays a pop-up message with an error about the invalid date.
//          * It is called when the 'end_date' is earlier than the 'start_date'.
//          *
//          * @private
//          */
//         _showDateErrorMessage: function () {
//             Dialog.alert(this, "Pastikan tanggal berakhir pelatihan tidak lebih awal dari tanggal mulai pelatihan!");
//         },
//     });
// });