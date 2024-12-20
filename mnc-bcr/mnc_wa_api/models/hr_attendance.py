from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

from odoo.addons.mnc_attendance.controllers.main import remove_seconds
import logging

_logger = logging.getLogger(__name__)


class HRAttendance(models.Model):
    _inherit = 'hr.attendance'

    def get_worked_time(self, duration):
        hours = int(duration)
        minutes = int((duration - hours) * 60)
        time_str = f"{hours} H {minutes} M"
        return time_str

    def attendance_durations(self, employee, date_check_in, date_check_out):
        attendance_ids = []
        domain = [('mncei_employee_id', '=', employee.id)]
        domain_ci = domain + [('check_in', '>=', date_check_in), ('check_in', '<=', date_check_out)]
        attendance_ci = self.env['hr.attendance'].sudo().search(domain_ci)
        # Get Chech Out
        domain_co = domain + [('check_out', '>=', date_check_in), ('check_out', '<=', date_check_out)]
        attendance_co = self.env['hr.attendance'].sudo().search(domain_co)
        # ==================================================================
        merged_set = set(attendance_ci).union(set(attendance_co))
        # Mengonversi kembali set ke daftar
        attendance_ids = list(merged_set)
        return attendance_ids

    def get_datas_attendance(self, employee_id, dates):
        res_data = []
        teams = employee_id.get_all_children_of_parent()
        for employee in teams:
            domain = [('mncei_employee_id', '=', employee.id)]
            # Get Today
            time_today = dates
            date_check_in = time_today - timedelta(hours=7)
            date_check_out = (time_today + timedelta(days=1)) - timedelta(hours=7)
            # Get Attendance
            attendance_ids = self.attendance_durations(employee, date_check_in, date_check_out)
            # time = 'N/A'
            if len(attendance_ids) > 0:
                for attendance in attendance_ids:
                    if employee.id == attendance.mncei_employee_id.id:
                        res_data.append({
                            'NIK': employee.nip_char,
                            'name': employee.nama_lengkap,
                            'company': employee.company.name,
                            'time_ci': remove_seconds(attendance.check_in, attendance.type_ci) if attendance.check_in else 'N/A',
                            'type_ci': attendance.type_ci,
                            'time_co': remove_seconds(attendance.check_out, attendance.type_co) if attendance.check_out else 'N/A',
                            'type_co': attendance.type_co,
                            'worked_hours': self.get_worked_time(attendance.worked_hours),
                        })
            else:
                res_data.append({
                    'NIK': employee.nip_char,
                    'name': employee.nama_lengkap,
                    'company': employee.company.name,
                    'time_ci': 'N/A',
                    'type_ci': '',
                    'time_co': 'N/A',
                    'type_co': '',
                    'worked_hours': "0 H 0 M",
                })
        return res_data

    # Mengurutkan berdasarkan time co yan
    def parse_time_co(self, record):
        if record['time_co'] == 'N/A':
            return datetime.min  # Tempatkan di akhir jika 'N/A'
        return datetime.strptime(record['time_co'], '%H:%M')

    @api.model
    def get_resume_att(self):
        today = fields.Date.today()
        last_7_days = []
        count = 1
        # Loop while untuk mendapatkan 7 tanggal ke belakang
        while count <= 7:
            day = today - timedelta(days=count)
            last_7_days.append(day)  # Format menjadi string (opsional)
            count += 1
        # Output hasil
        user_recipient_id = self.env['miners.recipient'].search([])
        dept_heads = self.env['miners.recipient.department'].search([('recipient_id', '=', user_recipient_id.id)])
        for dept_id in dept_heads:
            employee_ids = self.env['mncei.employee'].search([('department', '=', dept_id.department_id.id), ('active', '=', True)])
            for employee_id in employee_ids:
                datas = {
                    'employee_id': employee_id,
                    'last_7_days': last_7_days,
                }
                self.env["queue.job"].with_delay(
                    priority=None,
                    max_retries=None,
                    channel=None,
                    description=f"Resume Weekly {employee_id.nama_lengkap}",
                )._to_send_report(datas)
        return

    def send_resume_weekly(self, employee_id, last_7_days):
        if employee_id.roster_id:
            days_in_current_month = self.env['hr.leave']._get_number_of_days(datetime.combine(last_7_days[0], datetime.min.time()), datetime.combine(last_7_days[-1], datetime.max.time()), 2)
        else:
            days_in_current_month = self.env['hr.leave']._get_number_of_days(datetime.combine(last_7_days[0], datetime.min.time()), datetime.combine(last_7_days[-1], datetime.max.time()), 1)
        working_days = last_7_days[-int(days_in_current_month['days']):]
        datas = {}
        datas['planning'] = {
            'total_working_days': int(days_in_current_month['days']),
            'total_working_hours': int(days_in_current_month['hours']),
        }
        datas['actual'] = {
            'total_working_days': 0,
            'total_working_hours': 0,
            'avg_total_working_hours': 0,
            'total_absent': 0,
            'total_late': 0,
            'total_late_minutes': '',
        }
        datas['absent_weekly'] = {
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0,
            '7': 0,
        }
        datas['late_weekly'] = {
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0,
            '7': 0,
        }
        datas['total_sick'] = 0
        datas['total_leave'] = 0
        datas['total_punch'] = 0
        # Datas
        time_deltas = []
        worked_hours = []
        day = 1
        for work_day in working_days:
            check_in = datetime.combine(work_day, datetime.min.time()) - timedelta(hours=7)
            check_out = datetime.combine(work_day, datetime.max.time()) - timedelta(hours=7)
            # Get Attendance
            attendance_id = self.attendance_durations(employee_id, check_in, check_out)
            # Checking Dates
            if attendance_id:
                if attendance_id[0].type_ci == 'Alpha' or attendance_id[0].type_co == 'Alpha':
                    datas['actual']['total_absent'] += 1
                    if attendance_id[0].alpha_details == 'Sick':
                        datas['total_sick'] += 1
                    if attendance_id[0].alpha_details == 'Leave':
                        datas['total_leave'] += 1
                    datas['absent_weekly'][str(day)] = 1
                    datas['late_weekly'][str(day)] = 0
                elif attendance_id[0].type_ci != 'Alpha' or attendance_id[0].type_co != 'Alpha':
                    datas['actual']['total_working_days'] += 1
                    # late
                    if attendance_id[0].type_ci in ['Late']:
                        datas['absent_weekly'][str(day)] = 0
                        datas['late_weekly'][str(day)] = 1
                        time_diff = False
                        attendance = attendance_id[0]
                        if attendance.resouce_line_id or attendance.resouce_id:
                            ci_time_act = (attendance.check_in + timedelta(hours=7))
                            if attendance.resouce_line_id:
                                work_ci = attendance.resouce_line_id.hour_from
                            else:
                                if attendance.resouce_id.attendance_ids:
                                    work_ci = attendance.resouce_id.attendance_ids[0].hour_from
                            hours = int(work_ci + attendance.resouce_id.limit_attendance)
                            minutes = int(((work_ci + attendance.resouce_id.limit_attendance) - hours) * 60)
                            ci_time_plan = ci_time_act.replace(hour=hours, minute=minutes)
                            time_diff = ci_time_act - ci_time_plan
                        datas['actual']['total_late'] += 1
                        if time_diff:
                            hours_float = time_diff.total_seconds() / 3600
                            time_deltas.append(hours_float)
                worked_hours.append(attendance_id[0].worked_hours)
                # datas['actual']['total_working_hours'] += attendance_id[0].worked_hours
            else:
                datas['actual']['total_absent'] += 1
                datas['absent_weekly'][str(day)] = 1
                datas['late_weekly'][str(day)] = 0
            day += 1
        datas['actual']['total_working_hours'] = self.get_worked_time(sum(worked_hours))
        datas['actual']['avg_total_working_hours'] = self.get_worked_time((sum(worked_hours)/datas['actual']['total_working_days'])) if datas['actual']['total_working_days'] > 0 else "0 Jam 0 menit"
        datas['actual']['total_late_minutes'] = self.get_worked_time(sum(time_deltas)) if len(time_deltas) > 0 else "0 Jam 0 menit"
        punch_time = 0.0
        # Calc Punchtime
        if datas['actual']['total_working_days'] > 0 and sum(worked_hours) > 0:
            data_punch = {
                'total_working_days': datas['actual']['total_working_days'],
                'total_late_minutes': sum(time_deltas) * 60,
                'total_minute_days': (datas['planning']['total_working_hours']/datas['planning']['total_working_days'] * 60),
            }
            punch_time = self._calc_punchtime(data_punch)
        datas['total_punch'] = punch_time
        # Send Mail
        temp_weekly = self.env.ref('mnc_wa_api.notification_weekly_resume')
        temp_weekly.with_context(res_data=datas).send_mail(employee_id.id, force_send=True, email_values={'email_to': employee_id.email})

    def _calc_punchtime(self, datas):
        total_hari_kerja = datas['total_working_days']
        total_menit_terlambat = datas['total_late_minutes']
        total_menit_kerja_per_hari = datas['total_minute_days']
        # Menghitung total menit kerja aktual dalam seminggu
        total_menit_kerja_sebenarnya = (total_hari_kerja * total_menit_kerja_per_hari) - total_menit_terlambat
        # Menghitung persentase kehadiran tepat waktu berdasarkan menit kerja aktual
        total_menit_kerja_maksimal = total_hari_kerja * total_menit_kerja_per_hari
        total_punch = (total_menit_kerja_sebenarnya / total_menit_kerja_maksimal) * 100
        return round(total_punch, 2)

    # Send Resume Harian untuk dept head
    def send_report_resume_attendance(self):
        dept_heads = self.env['miners.recipient.department'].search([])
        for dept_id in dept_heads:
            if dept_id.user_ids:
                for user_id in dept_id.user_ids:
                    if user_id.mncei_employee_id:
                        employee_id = user_id.mncei_employee_id
                        today = datetime.combine(fields.Date.today(), datetime.min.time())
                        if today.weekday() == 0:
                            if employee_id.roster_id:
                                time = ((today - timedelta(days=1)) + timedelta(hours=7))
                            else:
                                time = ((today - timedelta(days=3)) + timedelta(hours=7))
                        else:
                            time = (today + timedelta(hours=7))
                        res_data = self.get_datas_attendance(employee_id, time)
                        # Filtering Data Lates
                        late_data = sorted([employee for employee in res_data if employee['time_ci'] != 'N/A' or employee['type_ci'] == 'Late'], key=lambda x: (x['time_ci'] != 'N/A', x['time_ci']))
                        # Filtering Data Early CI
                        earlist_ci = sorted([employee for employee in res_data if employee['time_ci'] != 'N/A'], key=lambda x: (x['time_ci'] != 'N/A', x['time_ci']))
                        # Filtering Data Lasted CO
                        lasted_co = sorted([employee for employee in res_data], key=lambda x: self.parse_time_co(x), reverse=True)
                        # Filtering Data Worked Hours
                        worked_hours = sorted([employee for employee in res_data if employee['time_ci'] != 'N/A'], key=lambda x: x['worked_hours'], reverse=True)
                        # Send Email to direct users
                        mail_template = self.env.ref('mnc_attendance.notification_resume_lastday').with_context(
                            dbname=self._cr.dbname,
                            late_data=late_data[:3],
                            early_ci_data=earlist_ci[:3],
                            last_co_data=lasted_co[:3],
                            working_data=worked_hours[:3],
                            today=time.strftime("%Y-%m-%d")
                        )
                        mail_template.send_mail(employee_id.id, force_send=True, email_values={'email_to': employee_id.email})
        return
