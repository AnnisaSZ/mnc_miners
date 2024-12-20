# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EmployeeSummaryReport(models.AbstractModel):
    _name = 'report.mnc_attendance.report_hr_attendance_document'
    _description = 'Attendance Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            docids = data['employees']
        att_reports = self.env['ir.actions.report']._get_report_from_name('mnc_attendance.report_hr_attendance_document')
        employees = self.env['mncei.employee'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': att_reports.model,
            'docs': employees,
            'data': data,
            'export_user': self.env.user.name,
            'attendance_data': data['attendance_data']
        }
