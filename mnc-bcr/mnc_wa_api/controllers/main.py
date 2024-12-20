import json
import base64
import math

from odoo import http, fields, SUPERUSER_ID, _
from odoo.http import request, content_disposition
from datetime import datetime, timedelta
from odoo.tools import html_escape

from odoo.addons.bcr_api_sh.controllers.main import BcrInterface
from odoo.addons.web.controllers.main import _serialize_exception

LIST_CI = [
    ('Alpha', 'Alpha'),
    ('CI_Ontime', 'Check In Ontime'),
    ('Late', 'Late'),
]

LIST_CO = [
    ('CO_Ontime', 'Check Out Ontime'),
    ('Overtime', 'Overtime'),
    ('Early_CO', 'Early Check Out'),
]


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


def get_employee(self):
    return request.env.user.mncei_employee_id or False


def is_valid_base64(base64_string):
    try:
        base64_bytes = base64.b64decode(base64_string)
        reencoded_base64 = base64.b64encode(base64_bytes)
        return reencoded_base64 == base64_string.encode('utf-8')
    except Exception as e:
        return False


def generate_result_status(datas):
    result = []
    type_in = []
    type_out = []

    for data in datas:
        for ci_item in LIST_CI:
            if data == ci_item[0]:
                type_in.append(data)
                break

        for co_item in LIST_CO:
            if data == co_item[0]:
                type_out.append(data)
                break

    if type_in and type_out:
        result.append('|')

    if type_in:
        result.append(('type_ci', 'in', type_in))
    if type_out:
        result.append(('type_co', 'in', type_out))
    return result


def get_sort_value(entry, sort_key):
    if sort_key == 'employee_name':
        return entry['employee_name']
    if sort_key == 'company_name':
        return entry['company_name']
    if sort_key == 'company_code':
        return entry['company_code']
    if sort_key == 'department_name':
        return entry['department_name']
    if sort_key == 'time_check_out':
        # Jika date_check_out kosong, gunakan date_check_in
        date_value = entry['date_check_out'] if entry['date_check_out'] else entry['date_check_in']
        time_value = entry['time_check_out'] if entry['time_check_out'] != '-' else '00:00'
    else:
        # Jika date_check_out kosong, gunakan date_check_in
        date_value = entry['date_check_in']
        time_value = entry['time_check_in'] if entry['time_check_in'] != '-' else '00:00'
    # Jika kondisi Date & Time Ada
    if date_value and time_value:
        dates = datetime.strptime(str(date_value) + " " + str(time_value), "%Y-%m-%d %H:%M")
        return dates
    else:
        return datetime.strptime(str(date_value), "%Y-%m-%d")


def paginate_data(data, page_number, items_per_page):
    total_items = len(data)
    total_pages = (total_items + items_per_page - 1) // items_per_page

    if page_number < 1 or page_number > total_pages:
        return {"error": "Invalid page number"}

    start_index = (page_number - 1) * items_per_page
    end_index = min(start_index + items_per_page, total_items)

    paginated_data = data[start_index:end_index]
    return {
        "total_pages": total_pages,
        "current_page": page_number,
        "data": paginated_data
    }


def remove_ontime_statuses(status_list):
    # Cek apakah "CI_Ontime" atau "CO_Ontime" ada dalam list
    if "CI_Ontime" in status_list:
        status_list[status_list.index("CI_Ontime")] = False
    if "CO_Ontime" in status_list:
        status_list[status_list.index("CO_Ontime")] = False
    return status_list


def get_time(self, times):
    hours, minute = convert_time(self, times)
    time = _("%s:%s") % (hours, minute)
    return time


def convert_time(self, time):
    factor = time < 0 and -1 or 1
    val = abs(time)
    # Hours
    hours = factor * int(math.floor(val))
    if hours > 0 and hours < 10:
        hours_char = '0' + str(hours)
    elif hours == 0:
        hours_char = '00'
    else:
        hours_char = str(factor * int(math.floor(val)))
    # Minutes
    minutes = int(round((val % 1) * 60))
    if minutes > 0 and minutes < 10:
        minutes_char = '0' + str(minutes)
    elif minutes == 0:
        minutes_char = '00'
    else:
        minutes_char = str(int(round((val % 1) * 60)))
    # Return Result
    return (hours_char, minutes_char)


def get_attachment(attendance_id, ttype=False):
    url = request.httprequest.host_url
    image_url = ''
    domain = [('res_id', '=', attendance_id.id), ('res_model', '=', 'hr.attendance'), ('company_id', '=', attendance_id.mncei_employee_id.company.id)]
    if ttype == 'check_in':
        domain += [('res_field', '=', 'check_in')]
    elif ttype == 'check_out':
        domain += [('res_field', '=', 'check_out')]
    attachment_id = request.env['ir.attachment'].search(domain, limit=1)
    if attachment_id:
        image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(attachment_id.id))
    return image_url


def remove_seconds(dt, category):
    if category in ['Alpha', 'Leave', 'Sick']:
        return '-'
    else:
        date = dt + timedelta(hours=7)
        dt_obj = fields.Datetime.from_string(date)
        hour = dt_obj.hour
        if hour > 9 and hour != 24:
            hours = str(hour)
        elif hour == 24 or hour > 24:
            hours = '00'
        else:
            hours = '0' + str(hour)
        minute = dt_obj.minute
        if minute > 9:
            minutes = str(minute)
        else:
            minutes = '0' + str(minute)
        times = _('%s:%s' % (hours, minutes))
        return times


def parameter_list(attendance_id):
    code_comp = request.env['master.bisnis.unit'].sudo().search([('bu_company_id', '=', attendance_id.mncei_employee_id.company.id)], limit=1).code
    data = {
        'id': attendance_id.id or 0,
        "is_leave": attendance_id.is_leave,
        'employee_id': attendance_id.mncei_employee_id.id or 0,
        'employee_name': attendance_id.mncei_employee_id.nama_lengkap or "",
        'company_id': attendance_id.mncei_employee_id.company.id or 0,
        'company_name': attendance_id.mncei_employee_id.company.name or "",
        'company_code': code_comp or "",
        'department_id': attendance_id.mncei_employee_id.department.id or 0,
        'department_name': attendance_id.mncei_employee_id.department.name or "",
    }
    if attendance_id.check_in:
        data.update({
            'date_check_in': (attendance_id.check_in + timedelta(hours=7)).date() or "",
            'time_check_in': remove_seconds(attendance_id.check_in, attendance_id.type_ci) or "",
            'category_ci': attendance_id.type_ci or "",
            'img_check_in': get_attachment(attendance_id, 'check_in') or ""
        })
    if not attendance_id.check_in:
        if attendance_id.check_out:
            data.update({
                'date_check_in': (attendance_id.check_out + timedelta(hours=7)).date() or "",
                'time_check_in': "",
                'category_ci': "",
                'img_check_in': get_attachment(attendance_id, 'check_in') or ""
            })
        else:
            data.update({
                'date_check_in': "",
                'time_check_in': "",
                'category_ci': "",
                'img_check_in': get_attachment(attendance_id, 'check_in') or ""
            })
    if attendance_id.check_out:
        data.update({
            'date_check_out': (attendance_id.check_out + timedelta(hours=7)).date() or "",
            'time_check_out': remove_seconds(attendance_id.check_out, attendance_id.type_co) or "",
            'category_co': attendance_id.type_co or "",
            'img_check_out': get_attachment(attendance_id, 'check_out') or ""
        })
    if not attendance_id.check_out:
        if attendance_id.check_in:
            data.update({
                'date_check_out': (attendance_id.check_in + timedelta(hours=7)).date() or "",
                'time_check_out': "",
                'category_co': attendance_id.type_co or "",
                'img_check_out': get_attachment(attendance_id, 'check_out') or ""
            })
        else:
            data.update({
                'date_check_out': "",
                'time_check_out': "",
                'category_co': "",
                'img_check_out': get_attachment(attendance_id, 'check_out') or ""
            })
    return data


def add_attachment(employee_id):
    attachment = request.env['ir.attachment'].create(
        {
            'name': employee_id.nama_lengkap,
            'company_id': employee_id.company.id,
            'public': True,
            'type': 'binary',
            'datas': employee_id.foto_pegawai,
            'res_model': 'mncei.employee',
            'res_field': 'foto_pegawai',
            'res_id': employee_id.id
        })
    return attachment


def float_to_time_str(float_val):
    # Mengonversi float menjadi detik total
    total_seconds = int(float_val * 3600)

    # Menghitung jam, menit, dan detik
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Membuat string format HH:MM:SS
    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"

    return time_str


class BcrInterface(BcrInterface):

    @http.route('/api/account/detail/get', type='json', auth="user")
    def getDataAccount(self, values=None):
        res = super(BcrInterface, self).getDataAccount(values)
        url = request.httprequest.host_url
        list_teams = []
        nik = ""
        jabatan = ""
        IUP = ""
        image_url = ""
        data_shift = {
            'start_ci': "00:00:00",
            'start_co': "14:00:00"
        }
        if res['code'] == 2:
            is_hr = False
            is_team_leads = False
            # ChecK Team Leads
            employee_id = get_employee(self)
            if employee_id:
                nik = employee_id.nip_char
                jabatan = employee_id.jabatan.name
                # Image Karyawan
                image_id = add_attachment(employee_id)
                image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(image_id.id))
                IUP = request.env['master.bisnis.unit'].sudo().search([('bu_company_id', '=', employee_id.company.id)], limit=1).code
                # Get Teams
                teams = employee_id.get_all_children_of_parent()
                list_teams = teams.ids
                if len(list_teams) > 0:
                    is_team_leads = True

                # Check Time Limit
                if employee_id.working_time_id or employee_id.shift_temp_ids:
                    if not employee_id.shift_temp_ids:
                        if employee_id.working_time_id:
                            start_ci = employee_id.working_time_id.attendance_ids[0].start_ci
                            start_co = employee_id.working_time_id.attendance_ids[0].start_co
                            data_shift['start_ci'] = float_to_time_str(start_ci)
                            data_shift['start_co'] = float_to_time_str(start_co)
                    else:
                        attendance_id = employee_id.shift_temp_ids.filtered(lambda x: x.start_date <= fields.Date.today() and x.end_date >= fields.Date.today())
                        if attendance_id:
                            if attendance_id.resouce_line_id:
                                start_ci = attendance_id.resouce_line_id.start_ci
                                start_co = attendance_id.resouce_line_id.start_co
                                data_shift['start_ci'] = float_to_time_str(start_ci)
                                data_shift['start_co'] = float_to_time_str(start_co)
                            else:
                                start_ci = attendance_id.working_time_id.attendance_ids[0].start_ci
                                start_co = attendance_id.working_time_id.attendance_ids[0].start_co
                                data_shift['start_ci'] = float_to_time_str(start_ci)
                                data_shift['start_co'] = float_to_time_str(start_co)
                        else:
                            start_ci = employee_id.working_time_id.attendance_ids[0].start_ci
                            start_co = employee_id.working_time_id.attendance_ids[0].start_co
                            data_shift['start_ci'] = float_to_time_str(start_ci)
                            data_shift['start_co'] = float_to_time_str(start_co)
            # Check HR
            if request.env.user.has_group('mnc_hr.group_hr_mgr') or request.env.user.has_group('mnc_hr.group_hr_user'):
                is_team_leads = False
                is_hr = True

            res['data']['is_hr'] = is_hr
            res['data']['is_team_leads'] = is_team_leads
            res['data']['IUP'] = IUP
            res['data']['NIK'] = nik
            res['data']['image_employee'] = image_url
            res['data']['jabatan'] = jabatan
            res['data']['time'] = data_shift

        return res


# class BcrAttendance(BcrInterface):
class MnceiAttendance(http.Controller):

    # Export
    @http.route(['/mnc_attendance/download'], type='http', auth="user")
    def get_report_xlsx(self, data, token):
        attendace_obj = request.env['hr.attendance']
        report_name = datetime.now().strftime('Attendance %Y-%m')
        records = list(map(int, data.strip('[]').split(',')))
        xlsx_data = attendace_obj.export_to_excel(records)
        content_base64 = base64.b64decode(xlsx_data.datas)
        # print(xlsx_data.datas)
        # print(base64.b64decode(xlsx_data.datas))
        # print(type(xlsx_data.datas))
        # # return attendace_obj.get_attachments_link(xlsx_data)
        # # return request.make_response('', headers=[('Location', act_url['url'])], status=302)
        # # response = {
        # #     'type': 'ir.actions.act_url',
        # #     'url': '/web/content/%s?download=true' % (xlsx_data.id),
        # # }
        response = request.make_response(
            content_base64,
            headers=[
                ('Content-Length', len(content_base64))
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(report_name + '.xlsx')),
            ]
        )
        response.set_cookie('fileToken', token)
        return response

    # Master
    @http.route('/api/att/master/employee', type='json', auth="public", csrf=False)
    def getDataEmployee(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_obj = request.env['mncei.employee']

                if request.env.user.has_group('mnc_hr.group_hr_mgr') or request.env.user.has_group('mnc_hr.group_hr_user'):
                    domain = [('state', '=', 'verified')]
                    if parameter['company_ids']:
                        domain += [('company', 'in', parameter['company_ids'])]
                    if parameter['department_ids']:
                        domain += [('department', 'in', parameter['department_ids'])]
                    if parameter['name']:
                        domain += [('nama_lengkap', 'ilike', parameter['name'])]
                    # Get Search
                    employee_ids = employee_obj.sudo().search(domain)
                    if employee_ids:
                        for emp_id in employee_ids:
                            res_data.append({
                                'NIK': emp_id.nip_char,
                                'name': emp_id.nama_lengkap,
                            })
                else:
                    employee_id = get_employee(self)
                    if not employee_id:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": "Please create relation user to employee in Odoo"
                        }
                        return result
                    teams = employee_id.get_all_children_of_parent()
                    list_teams = teams.ids
                    list_teams.append(employee_id.id)
                    if len(list_teams) > 0:
                        for emp_id in list_teams:
                            domain = [('id', '=', emp_id)]
                            employee_id = employee_obj.sudo().search(domain)
                            res_data.append({
                                'NIK': employee_id.nip_char,
                                'name': employee_id.nama_lengkap,
                            })

                result = {
                    "code": 2,
                    "desc": "Success",
                    "data": res_data
                }
                return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
                return result

    @http.route('/api/att/master/status', type='json', auth="public", csrf=False)
    def getDataStatus(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                all_state = LIST_CI + LIST_CO
                for state in all_state:
                    res_data.append({
                        'code': state[0],
                        'name': state[1],
                    })

                result = {
                    "code": 2,
                    "desc": "Success",
                    "data": res_data
                }
                return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
                return result

    @http.route('/api/att/master/department', type='json', auth="public", csrf=False)
    def getDataDepartment(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                domain = [('state', '=', 'active')]
                department_ids = request.env['mncei.department'].sudo().search(domain)
                for department_id in department_ids:
                    res_data.append({
                        'id': department_id.id,
                        'name': department_id.name,
                    })

                result = {
                    "code": 2,
                    "desc": "Success",
                    "data": res_data
                }
                return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
                return result

    @http.route('/api/att/master/location', type='json', auth="public", csrf=False)
    def getDataLocationAtt(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(self)

                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result
                else:
                    date = datetime.strptime(parameter["date"], '%Y-%m-%d')
                    working_time = employee_id.get_working_time(date.date())
                    if not working_time:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": "Please create Working Time/Shif in Employee Odoo"
                        }
                        return result
                    location_ids = request.env["res.att.location"].search([('loc_working_id', '=', working_time.loc_working_id.id), ('status', '=', 'active')])

                    if location_ids:
                        for location_id in location_ids:
                            res_data.append({
                                'id': location_id.id,
                                'name': location_id.name,
                                'longitude': location_id.longitude,
                                'latitude': location_id.latitude,
                                'limit_distance': location_id.limit_location
                                # 'allowed_distance': location_id.allowed_location
                            })

                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
            else:
                result = {"code": 4,
                          "desc": 'Access Denied'}
                return result

    # History
    @http.route('/api/att/history/team_list', type='json', auth="public", csrf=False)
    def getDataListTeams(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = []
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(self)
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                if not parameter["date_start"] or not parameter["date_end"]:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please input date"
                    }
                    return result

                is_hr = False
                is_team_leads = False
                # ChecK Team Leads
                employee_id = get_employee(self)
                if employee_id:
                    # Get Teams
                    teams = employee_id.get_all_children_of_parent()
                    list_teams = teams.ids
                    if len(list_teams) > 0:
                        is_team_leads = True
                # Check HR
                if request.env.user.has_group('mnc_hr.group_hr_mgr') or request.env.user.has_group('mnc_hr.group_hr_user'):
                    is_hr = True
                    is_team_leads = False

                # ===================== Team Leads =====================
                if is_team_leads:
                    # Get Teams
                    teams = employee_id.get_all_children_of_parent()
                    list_teams = teams.ids
                    # Add Current Employee
                    list_teams.append(employee_id.id)
                    # Domain
                    if parameter['emp_nik'] or parameter['company_ids']:
                        emp_domain = []
                        if parameter['emp_nik']:
                            emp_domain = [('nip_char', '=', parameter['emp_nik'])]
                        if parameter['company_ids']:
                            emp_domain += [('company', 'in', parameter['company_ids'])]
                        # Get Employee
                        employee_ids = request.env['mncei.employee'].sudo().search(emp_domain)
                        if employee_ids:
                            employees = []
                            for employee_id in employee_ids:
                                if employee_id.id in list_teams:
                                    employees.append(employee_id.id)
                            list_teams = employees
                        else:
                            list_teams = []

                    for emp_id in list_teams:
                        # Check Data
                        date_check_in = datetime.strptime(str(parameter['date_start']), "%Y-%m-%d") - timedelta(hours=7)
                        date_check_out = datetime.strptime(str(parameter['date_end']), "%Y-%m-%d") - timedelta(hours=7)
                        # date_check_out = _('%s 23:59:00' % (parameter['date_end']))
                        domain += [('mncei_employee_id', '=', emp_id)]
                        if parameter["status"]:
                            status = generate_result_status(parameter["status"])
                            domain += status

                        # Get Datas
                        # ==================================================================
                        # Check In
                        domain_ci = domain + [('check_in', '>=', date_check_in), ('check_in', '<=', date_check_out)]
                        attendance_ci = request.env['hr.attendance'].sudo().search(domain_ci)
                        # Check Out
                        domain_co = domain + [('check_out', '>=', date_check_in), ('check_out', '<=', date_check_out)]
                        attendance_co = request.env['hr.attendance'].sudo().search(domain_co)
                        # ==================================================================
                        merged_set = set(attendance_ci).union(set(attendance_co))
                        # Mengonversi kembali set ke daftar
                        attendance_ids = list(merged_set)
                        # ==================================================================
                        domain = []
                        for att_id in attendance_ids:
                            res_data.append(parameter_list(att_id))
                # ===================== HR Teams =====================
                elif is_hr:
                    emp_domain = []
                    if parameter['company_ids']:
                        emp_domain += [('company', 'in', parameter['company_ids'])]
                    if parameter['department_ids']:
                        emp_domain += [('department', 'in', parameter['department_ids'])]
                    # Just Emp if search by employee
                    if parameter['emp_nik']:
                        emp_domain += [('nip_char', '=', parameter['emp_nik'])]
                    # Get Search
                    employee_ids = request.env['mncei.employee'].sudo().search(emp_domain)
                    if employee_ids:
                        for emp_id in employee_ids:
                            # date_check_in = _('%s 00:00:00' % (parameter['date_start']))
                            date_check_in = datetime.strptime(str(parameter['date_start']), "%Y-%m-%d") - timedelta(hours=7)
                            date_check_out = datetime.strptime(str(parameter['date_end']), "%Y-%m-%d") - timedelta(hours=7)
                            # date_check_out = _('%s 23:59:00' % (parameter['date_end']))
                            domain += [('mncei_employee_id', '=', emp_id.id)]
                            if parameter["status"]:
                                status = generate_result_status(parameter["status"])
                                domain += status

                            # Get Data
                            # ==============================================
                            # Check In
                            domain_ci = domain + [('check_in', '>=', date_check_in), ('check_in', '<=', date_check_out)]
                            attendance_ci = request.env['hr.attendance'].sudo().search(domain_ci)
                            # Check In
                            domain_co = domain + [('check_out', '>=', date_check_in), ('check_out', '<=', date_check_out)]
                            attendance_co = request.env['hr.attendance'].sudo().search(domain_co)
                            # ==============================================
                            merged_set = set(attendance_ci).union(set(attendance_co))
                            # Mengonversi kembali set ke daftar
                            attendance_ids = list(merged_set)
                            domain = []
                            for att_id in attendance_ids:
                                res_data.append(parameter_list(att_id))
                # ===================================================================================
                # Jumlah total halaman
                page_number = int(request.httprequest.args.get('page')) 
                if res_data:
                    if parameter['sort']:
                        if parameter['sort'] == 'desc':
                            res_data = sorted(res_data, key=lambda x: get_sort_value(x, parameter["type_sort"]), reverse=True)
                        else:
                            res_data = sorted(res_data, key=lambda x: get_sort_value(x, parameter["type_sort"]), reverse=False)
                    # ==============================================
                    items_per_page = 10  # Example items per page

                    total_pages = (len(res_data) + items_per_page - 1) // items_per_page
                    if page_number > total_pages or page_number <= 0:
                        result = {
                            "code": 3,
                            "desc": "pages must be below the total page",
                            "data": [],
                        }
                        return result
                    # Call the paginate_data function
                    paginated_result = paginate_data(res_data, page_number, items_per_page)
                else:
                    total_pages = 1
                    paginated_result = {'data': []}
                # ===================================================================================
                result = {
                    "code": 2,
                    "desc": "Success",
                    "total_pages": total_pages,
                    "page": page_number,
                    "data": paginated_result['data']
                }
                return result
        else:
            result = {
                "code": 4,
                "desc": 'Access Denied'
            }
            return result

    @http.route('/api/att/history/teams', type='json', auth="public", csrf=False)
    def getDataTeams(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                # domain = []
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                attendance_obj = request.env['hr.attendance']
                employee_id = get_employee(self)
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result
                if not parameter["date"]:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please input date"
                    }
                    return result
                else:
                    date = datetime.strptime(parameter["date"], '%Y-%m-%d')
                    # Get Teams
                    teams = employee_id.get_all_children_of_parent()
                    list_teams = teams.ids
                    # Add Current Employee
                    list_teams.append(employee_id.id)
                    detail = attendance_obj.get_data_present(date.date(), list_teams)
                    att_detail = {
                        'total_teams': len(list_teams),
                        'total_present': detail.get('total'),
                        'total_late': detail.get('late'),
                        'total_early_co': detail.get('early_co'),
                        'total_ot': detail.get('ot')
                    }
                    res_data.append(att_detail)

                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
        else:
            result = {
                "code": 4,
                "desc": 'Access Denied'
            }
            return result

    @http.route('/api/att/history/get_today', type='json', auth="public", csrf=False)
    def getDates(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = []
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(self)
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result
                # Domain
                domain += [('mncei_employee_id', '=', employee_id.id)]
                # ====================================================
                # Working Time
                working_time = {}
                if not employee_id.shift_temp_ids:
                    if employee_id.working_time_id:
                        start_ci = employee_id.working_time_id.attendance_ids[0].start_ci
                        start_co = employee_id.working_time_id.attendance_ids[0].start_co
                        working_time['id'] = employee_id.working_time_id.id
                        working_time['start_ci'] = float_to_time_str(start_ci)
                        working_time['start_co'] = float_to_time_str(start_co) if start_co != 0.0 else None
                        # Working Time
                        time_start = get_time(self, employee_id.working_time_id.attendance_ids[0].hour_from)
                        time_end = get_time(self, employee_id.working_time_id.attendance_ids[0].hour_to)
                        working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                    else:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": "Please call HRD, you're not allowed working time"
                        }
                        return result
                else:
                    attendance_id = employee_id.shift_temp_ids.filtered(lambda x: x.start_date <= fields.Date.today() and x.end_date >= fields.Date.today())
                    if attendance_id:
                        if attendance_id.resouce_line_id:
                            start_ci = attendance_id.resouce_line_id.start_ci
                            start_co = attendance_id.resouce_line_id.start_co
                            working_time['id'] = attendance_id.working_time_id.id
                            working_time['start_ci'] = float_to_time_str(start_ci)
                            working_time['start_co'] = float_to_time_str(start_co) if start_co != 0.0 else None
                            # Working Time
                            time_start = get_time(self, attendance_id.resouce_line_id.hour_from)
                            time_end = get_time(self, attendance_id.resouce_line_id.hour_to)
                            working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                        else:
                            start_ci = attendance_id.working_time_id.attendance_ids[0].start_ci
                            start_co = attendance_id.working_time_id.attendance_ids[0].start_co
                            working_time['id'] = attendance_id.working_time_id.id
                            working_time['start_ci'] = float_to_time_str(start_ci)
                            working_time['start_co'] = float_to_time_str(start_co) if start_co != 0.0 else None
                            # Working Time
                            time_start = get_time(self, attendance_id.resouce_line_id.hour_from)
                            time_end = get_time(self, attendance_id.resouce_line_id.hour_to)
                            working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                    else:
                        start_ci = employee_id.working_time_id.attendance_ids[0].start_ci
                        start_co = employee_id.working_time_id.attendance_ids[0].start_co
                        working_time['id'] = employee_id.working_time_id.id
                        working_time['start_ci'] = float_to_time_str(start_ci)
                        working_time['start_co'] = float_to_time_str(start_co) if start_co != 0.0 else None
                        # Working Time
                        time_start = get_time(self, employee_id.working_time_id.attendance_ids[0].hour_from)
                        time_end = get_time(self, employee_id.working_time_id.attendance_ids[0].hour_to)
                        working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                # ==================================================================
                today = fields.Date.today()
                # Tipe data string untuk waktu
                waktu = working_time['start_ci']
                start_time = (datetime.strptime(f"{today} {waktu}", "%Y-%m-%d %H:%M:%S"))
                time_today = (fields.Datetime.now() + timedelta(hours=7)).hour
                # if 23 > start_time.hour:
                if time_today > start_time.hour:
                    # Ambil Hari ini
                    date_check_in = start_time - timedelta(hours=7)
                    date_check_out = (start_time + timedelta(days=1)) - timedelta(hours=7)
                else:
                    # Ambil Kemarin
                    date_check_in = (start_time - timedelta(days=1)) - timedelta(hours=7)
                    date_check_out = start_time - timedelta(hours=7)

                # Get Chech In
                domain_ci = domain + [('check_in', '>=', date_check_in), ('check_in', '<=', date_check_out)]
                attendance_ci = request.env['hr.attendance'].sudo().search(domain_ci)
                # Get Chech Out
                domain_co = domain + [('check_out', '>=', date_check_in), ('check_out', '<=', date_check_out)]
                attendance_co = request.env['hr.attendance'].sudo().search(domain_co)
                # ==================================================================
                merged_set = set(attendance_ci).union(set(attendance_co))
                # Mengonversi kembali set ke daftar
                attendance_ids = list(merged_set)
                for att_id in attendance_ids:
                    res_data.append(parameter_list(att_id))

                result = {
                    "code": 2,
                    "desc": "Success",
                    "working_time": working_time,
                    "data": res_data
                }
                return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
            return result

    @http.route('/api/att/history/mylist', type='json', auth="public", csrf=False)
    def getMyHistories(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = []
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(self)
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                # Domain
                date_format = "%Y-%m-%d"
                date_start = datetime.strptime(parameter['date_start'], date_format).date()
                date_end = datetime.strptime(parameter['date_end'], date_format).date()
                # Get Time
                date_check_in = datetime.combine(date_start, datetime.min.time()) - timedelta(hours=7)
                date_check_out = datetime.combine(date_end, datetime.max.time()) - timedelta(hours=7)
                domain += [('mncei_employee_id', '=', employee_id.id)]
                if parameter["status"]:
                    status = generate_result_status(parameter["status"])
                    domain += status

                # Get Working Time
                working_time = {}
                # working_time_id = False
                # is_shift = False
                if not employee_id.shift_temp_ids:
                    if employee_id.working_time_id:
                        start_ci = employee_id.working_time_id.attendance_ids[0].start_ci
                        start_co = employee_id.working_time_id.attendance_ids[0].start_co
                        working_time['start_ci'] = float_to_time_str(start_ci)
                        working_time['start_co'] = float_to_time_str(start_co) if start_co != 0.0 else None
                        # Working Time
                        time_start = get_time(self, employee_id.working_time_id.attendance_ids[0].hour_from)
                        time_end = get_time(self, employee_id.working_time_id.attendance_ids[0].hour_to)
                        working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                else:
                    attendance_id = employee_id.shift_temp_ids.filtered(lambda x: x.start_date <= fields.Date.today() and x.end_date >= fields.Date.today())
                    if attendance_id:
                        if attendance_id.resouce_line_id:
                            start_ci = attendance_id.resouce_line_id.start_ci
                            start_co = attendance_id.resouce_line_id.start_co
                            working_time['start_ci'] = float_to_time_str(start_ci)
                            working_time['start_co'] = float_to_time_str(start_co) if start_co != 0.0 else None
                            # Working Time
                            time_start = get_time(self, attendance_id.resouce_line_id.hour_from)
                            time_end = get_time(self, attendance_id.resouce_line_id.hour_to)
                            working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                        else:
                            start_ci = attendance_id.working_time_id.attendance_ids[0].start_ci
                            start_co = attendance_id.working_time_id.attendance_ids[0].start_co
                            working_time['start_ci'] = float_to_time_str(start_ci)
                            working_time['start_co'] = float_to_time_str(start_co) if start_co != 0.0 else None
                            # Working Time
                            time_start = get_time(self, attendance_id.resouce_line_id.hour_from)
                            time_end = get_time(self, attendance_id.resouce_line_id.hour_to)
                            working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                    else:
                        start_ci = employee_id.working_time_id.attendance_ids[0].start_ci
                        start_co = employee_id.working_time_id.attendance_ids[0].start_co
                        working_time['start_ci'] = float_to_time_str(start_ci)
                        working_time['start_co'] = float_to_time_str(start_co) if start_co != 0.0 else None
                        # Working Time
                        time_start = get_time(self, employee_id.working_time_id.attendance_ids[0].hour_from)
                        time_end = get_time(self, employee_id.working_time_id.attendance_ids[0].hour_to)
                        working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                # ==================================================================
                # Get Chech In
                domain_ci = domain + [('check_in', '>=', date_check_in), ('check_in', '<=', date_check_out)]
                attendance_ci = request.env['hr.attendance'].sudo().search(domain_ci)
                # Get Chech Out
                domain_co = domain + [('check_out', '>=', date_check_in), ('check_out', '<=', date_check_out)]
                attendance_co = request.env['hr.attendance'].sudo().search(domain_co)
                # ==================================================================
                merged_set = set(attendance_ci).union(set(attendance_co))
                # Mengonversi kembali set ke daftar
                attendance_ids = list(merged_set)
                for att_id in attendance_ids:
                    res_data.append(parameter_list(att_id))
                # =====================================================
                page_number = int(request.httprequest.args.get('page'))  # Example page number
                if res_data:
                    if parameter['sort']:
                        if parameter['sort'] == 'desc':
                            res_data = sorted(res_data, key=lambda x: get_sort_value(x, parameter["type_sort"]), reverse=True)
                        else:
                            res_data = sorted(res_data, key=lambda x: get_sort_value(x, parameter["type_sort"]), reverse=False)
                    # =====================================================
                    items_per_page = 10  # Example items per page

                    total_pages = (len(res_data) + items_per_page - 1) // items_per_page
                    if page_number > total_pages or page_number <= 0:
                        result = {
                            "code": 3,
                            "desc": "pages must be below the total page",
                            "data": [],
                        }
                        return result
                    # Call the paginate_data function
                    paginated_result = paginate_data(res_data, page_number, items_per_page)
                else:
                    total_pages = 1
                    paginated_result = {'data': []}
                # =====================================================
                result = {
                    "code": 2,
                    "desc": "Success",
                    "total_pages": total_pages,
                    "page": page_number,
                    "working_time": working_time,
                    "data": paginated_result['data']
                }
                return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
            return result

    @http.route('/api/att/history/details', type='json', auth="public", csrf=False)
    def getDetails(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            url = request.httprequest.host_url
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                # ======== Check Parameter ========
                employee_id = get_employee(self)
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result
                # Get Datas
                att_id = request.env['hr.attendance'].search([('id', '=', parameter['id'])], limit=1) or False
                if not att_id:
                    result = {
                        "code": 3,
                        "desc": "ID Not Found",
                    }
                    return result
                else:
                    # Get Profile
                    profile = {}
                    employee_id = att_id.mncei_employee_id
                    nik = employee_id.nip_char
                    jabatan = employee_id.jabatan.name
                    # Image Karyawan
                    image_id = add_attachment(employee_id)
                    image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(image_id.id))
                    IUP = request.env['master.bisnis.unit'].sudo().search([('bu_company_id', '=', employee_id.company.id)], limit=1).code
                    profile['profile'] = {
                        'name': employee_id.nama_lengkap,
                        'nik': nik,
                        'IUP': IUP,
                        'jabatan': jabatan,
                        'image_employee': image_url,
                    }
                    res_data.append(profile)
                    # Get Working Hours
                    working_time = {}
                    if att_id.resouce_line_id:
                        # Start
                        time_start = get_time(self, att_id.resouce_line_id.hour_from)
                        # End
                        time_end = get_time(self, att_id.resouce_line_id.hour_to)
                        working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                    else:
                        # Start
                        time_start = get_time(self, att_id.resouce_id.attendance_ids[0].hour_from)
                        # End
                        time_end = get_time(self, att_id.resouce_id.attendance_ids[0].hour_to)
                        working_time['working_time'] = _("%s - %s") % (time_start, time_end)
                    res_data.append(working_time)
                    # Get Detail
                    detail = {}
                    detail['check_in'] = None
                    detail['check_out'] = None
                    if att_id.check_in:
                        detail['check_in'] = {
                            'date_ci': att_id.check_in.date() or "",
                            'time_ci': remove_seconds(att_id.check_in, att_id.type_ci) or "",
                            # 'time_ci': (att_id.check_in + timedelta(hours=7)).time() or "",
                            'location_ci_id': att_id.location_ci_id.id or 0,
                            'location_ci': att_id.location_ci_id.name or "",
                            'other_location_ci': att_id.location_ci_notes or "",
                            'img_check_in': get_attachment(att_id, 'check_in') or "",
                            'remarks_ci': att_id.remarks_ci or "",
                            'category_ci': att_id.type_ci or "",
                        }
                    if att_id.check_out:
                        detail['check_out'] = {
                            'date_co': att_id.check_out.date() or "",
                            'time_co': remove_seconds(att_id.check_out, att_id.type_ci) or "",
                            # 'time_co': (att_id.check_out + timedelta(hours=7)).time() or "",
                            'location_co_id': att_id.location_co_id.id or 0,
                            'location_co': att_id.location_co_id.name or "",
                            'other_location_co': att_id.location_co_notes or "",
                            'img_check_out': get_attachment(att_id, 'check_out') or "",
                            'remarks_co': att_id.remarks_co or "",
                            'category_co': att_id.type_co or "",
                        }
                    res_data.append(detail)

                result = {
                    "code": 2,
                    "desc": "Success",
                    "data": res_data
                }
                return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
            return result

    # Action
    @http.route('/api/att/action/submit', type='json', auth="public", csrf=False)
    def InputDataAtt(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                # domain = []
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                # Check paramater if empty
                time_list = []
                for params in parameter:
                    if params == 'date' or params == 'time':
                        time_list.append(parameter[params])
                date_time = datetime.strptime(' '.join(time_list), "%Y-%m-%d %H:%M:%S") - timedelta(hours=7)
                employee_id = get_employee(self)
                # Check Parameter
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result
                if not parameter['location'] and parameter['location'] != 0:
                    result = {
                        "code": 3,
                        "desc": 'Please Input Location'
                    }
                    return result
                if not parameter['photo']:
                    result = {
                        "code": 3,
                        "desc": 'Please Input Your Photo'
                    }
                    return result
                # Check Location
                location_id = request.env['res.att.location'].browse(parameter['location']) or False
                if not location_id:
                    if parameter['location'] == 0:
                        location_id = request.env['res.att.location'].search([('is_other', '=', True)], limit=1) or False
                        if not location_id:
                            result = {
                                "code": 3,
                                "desc": 'Location Not Found'
                            }
                            return result
                    else:
                        result = {
                            "code": 3,
                            "desc": 'Location Not Found'
                        }
                        return result
                # Check Image
                check_image = is_valid_base64(parameter['photo'])
                if not check_image:
                    result = {
                        "code": 3,
                        "desc": "Please check your image"}
                    return result
                # Create Attendance
                att_obj = request.env['hr.attendance']
                att_id = att_obj.to_create(date_time, employee_id, location_id, parameter)
                if att_id:
                    res_data.append({'id': att_id.id})
                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "desc": "Please check your data"}
                    return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
            return result
