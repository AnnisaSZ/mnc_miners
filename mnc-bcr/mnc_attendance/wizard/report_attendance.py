# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from datetime import datetime, timedelta


class ReportAttendance(models.TransientModel):
    _name = "attendance.report.wizard"
    _description = "Resource Calendar Wizard"

    company_id = fields.Many2one('res.company', string="Company", required=True)
    show_button_data = fields.Boolean(string="Start Date")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    employee_id = fields.Many2one('mncei.employee', string="Employee", domain="[('company', '=', company_id)]")
    employee_ids = fields.Many2many('mncei.employee', string="Employee", domain="[('company', '=', company_id)]")

    def generate_report(self):
        if self.employee_ids:
            attendance_data, employees = self.env['mncei.employee'].get_attendance_data_by_employee(
                self.employee_ids.ids, self.start_date, self.end_date)
        else:
            attendance_data, employees = self.env['mncei.employee'].get_attendance_data_by_company(
                self.company_id.id, self.start_date, self.end_date)
        data = {
            'company_id': self.company_id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'attendance_data': attendance_data,
            'employees': employees,
        }
        return self.env.ref('mnc_attendance.action_hr_attendance_report').report_action(None, data=data)

    def get_datas_manual(self):
        employees = self.employee_ids
        fmt = '%Y-%m-%d'
        d1 = datetime.strptime(str(self.start_date), fmt)
        d2 = datetime.strptime(str(self.end_date), fmt)
        daysDiff = (d2-d1).days + 1

        for date in range(daysDiff):
            start = d1 + timedelta(days=date)
            end = start + timedelta(hours=23) + timedelta(minutes=59)

            if not self.employee_ids and self.company_id:
                attendance_data, employees = self.env['mncei.employee'].get_attendance_data_by_company(self.company_id.id, start, end)
                self.employee_ids = self.env['mncei.employee'].search([('id', 'in', employees)])

            for employee in self.employee_ids:
                employee_code = employee.wdms_code
                shift = employee.shift_temp_ids.filtered(lambda x: x.start_date <= start and x.end_date >= end)
                is_shift = False
                if shift:
                    is_shift = True
                datas = {
                    'start_date': start,
                    'end_date': end,
                    'employee_code': employee_code,
                    'is_shift': is_shift
                }
                self.env["queue.job"].with_delay(
                    priority=None,
                    max_retries=None,
                    channel=None,
                    description="Attendance",
                )._create_attendance(datas)
        return
