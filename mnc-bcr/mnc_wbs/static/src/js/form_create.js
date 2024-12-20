odoo.define('mnc_wbs.form_create', function (require) {
    'use strict';

    var core = require('web.core');
    var ajax = require('web.ajax');
    var session = require('web.session');
    var _t = core._t;

    // Define a function to check the current URL and perform the redirection
    function checkAndRedirect() {
        var currentPath = window.location.pathname;
        if (currentPath === '/my' || currentPath === '/my/home') {
            window.location.href = '/wbs/home';
        }
    }

    $(document).ready(function () {

        checkAndRedirect();

        var MAX_SIZE_MB = 5;
        var MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024; // 5MB in bytes

        // Function to check file size
        function checkFileSize(fileInput) {
            var files = fileInput[0].files;
            for (var i = 0; i < files.length; i++) {
                if (files[i].size > MAX_SIZE_BYTES) {
                    alert('File "' + files[i].name + '" exceeds the maximum size of 5MB.');
                    fileInput.val(''); // Clear the file input
                    return false;
                }
            }
            return true;
        }

        // Add event listener to each file input
        $('input[type="file"]').on('change', function () {
            checkFileSize($(this));
        });

        // Hide buttons initially
        $('#submit').hide();
        $('#draft').hide();

        // Ensure checkbox is unchecked and disabled by default
        $('#tnc_button').prop('checked', false);
        $('#tnc_button').prop('disabled', true);
        
        // Function to toggle buttons based on checkbox status
        function toggleButtons() {

            var isChecked = $('#tnc_button').is(':checked');
            if (isChecked) {
                $('#submit').show();
                $('#draft').show();
            } else {
                $('#submit').hide();
                $('#draft').hide();
            }
        }

        // Function to check if the user has scrolled to the bottom of T&C
        function checkScrollPosition() {
            var textarea = $('#tnc');
            var scrollHeight = textarea[0].scrollHeight - 100;
            var scrollTop = textarea.scrollTop();
            var clientHeight = textarea.height();
            var hasScrolledToBottom = scrollTop + clientHeight >= scrollHeight;

            if (hasScrolledToBottom) {
                $('#tnc_button').prop('disabled', false); // Enable checkbox
            } else {
                $('#tnc_button').prop('disabled', true); // Disable checkbox
                $('#tnc_button').prop('checked', false); // Uncheck checkbox if not scrolled to bottom
                toggleButtons();
            }
        }

        // Add event listener to textarea for scroll position
        $('#tnc').on('scroll', function () {
            checkScrollPosition();
        });

        // Add event listener to checkbox
        $('#tnc_button').on('change', function () {
            toggleButtons();
        });

        // Check checkbox status on page load
        toggleButtons();

        // Additional JavaScript code

        // Set selected option for company_id_report
        var companyIdElement = document.getElementById('company_id');
        var companyReportElement = document.getElementById('company_id_report');

        if (companyIdElement && companyReportElement) {
            var company_id = companyIdElement.value;

            // Get Selected Company
            for(var i, j = 0; i = companyReportElement.options[j]; j++) {
                if(i.value == company_id) {
                    companyReportElement.selectedIndex = j;
                }
            }
        }

        // Clear Input Attachment
        function resetInput(id) {
            var inputElement = document.getElementById("Input" + id);
            if (inputElement) {
                inputElement.value = "";
            }
        }
    });
});
