from odoo import http, _
from odoo.http import request
from datetime import datetime, timedelta

from odoo.addons.mnc_attendance.controllers.main import remove_seconds
import logging

_logger = logging.getLogger(__name__)


class AttendanceHistory(http.Controller):

    @http.route('/attendance', auth='public', website=True)
    def get_attendance_datas(self, values=None):
        date_object = datetime.strptime(str(request.httprequest.args.get('date')), "%d%m%Y")
        user_id = request.env['res.users'].sudo().browse(int(request.httprequest.args.get('uid')))
        res_data = []
        if user_id.mncei_employee_id:
            teams = user_id.mncei_employee_id.get_all_children_of_parent()
            for employee_id in teams:
                domain = [('mncei_employee_id', '=', employee_id.id)]
                time_today = date_object
                date_check_in = time_today
                date_check_out = (date_check_in + timedelta(days=1))
                # Get Attendance
                domain_ci = domain + [('check_in', '>=', date_check_in), ('check_in', '<=', date_check_out)]
                attendance_ci = request.env['hr.attendance'].sudo().search(domain_ci)
                # Get Chech Out
                domain_co = domain + [('check_out', '>=', date_check_in), ('check_out', '<=', date_check_out)]
                attendance_co = request.env['hr.attendance'].sudo().search(domain_co)
                # ==================================================================
                merged_set = set(attendance_ci).union(set(attendance_co))
                # Mengonversi kembali set ke daftar
                attendance_ids = list(merged_set)
                time = 'N/A'
                time_diff = False
                is_working = employee_id._is_work(time_today)
                if is_working:
                    if len(attendance_ids) > 0:
                        _logger.info("ZZZZZZZZZZZZZZZZZZZZZZZZZ00")
                        for attendance in attendance_ids:
                            time = remove_seconds(attendance.check_in, attendance.type_ci)
                            if employee_id.id == attendance.mncei_employee_id.id:
                                if attendance.type_ci in ['Alpha', 'Late']:
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
                                    res_data.append({
                                        'NIK': employee_id.nip_char,
                                        'name': employee_id.nama_lengkap,
                                        'time': time,
                                        'time_diff': time_diff,
                                    })
                    else:
                        _logger.info("ZZZZZZZZZZZZZZZZZZZZZZZZZ01")
                        res_data.append({
                            'NIK': employee_id.nip_char,
                            'name': employee_id.nama_lengkap,
                            'time': time,
                            'time_diff': time_diff
                        })

        data = sorted(res_data, key=lambda x: x['time_diff'] if isinstance(x['time_diff'], timedelta) else timedelta.min, reverse=True)
        return request.render('mnc_wa_api.template_user_lates', {'user_data': data})
