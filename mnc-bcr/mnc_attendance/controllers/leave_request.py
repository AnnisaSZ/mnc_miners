import json
import base64
import math

from odoo import http, fields, SUPERUSER_ID, _
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

from odoo.addons.bcr_api_sh.controllers.main import BcrInterface


def is_valid_base64(base64_string):
    try:
        base64_bytes = base64.b64decode(base64_string)
        reencoded_base64 = base64.b64encode(base64_bytes)
        return reencoded_base64 == base64_string.encode('utf-8')
    except Exception as e:
        return False


def search_leave_by_id(res_id):
    leave_id = request.env['hr.leave'].search([('id', '=', res_id)])
    return leave_id


def get_datetime(entry):
    request_date = entry["create_date"]
    return request_date


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


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


def get_employee(user):
    return user.mncei_employee_id or False


def get_cartaker(employee_id):
    user_id = request.env['res.users'].search([('mncei_employee_id', '=', employee_id)])
    return user_id


def get_approval(leave_id, state=False):
    datas = []
    approval_model = request.env['hr.leave.approval']
    for approval in leave_id.approval_ids:
        employee_id = get_employee(approval.user_id)
        if employee_id:
            datas.append({
                'id': approval.id or 0,
                'user_id': approval.user_id.id or 0,
                'caretaker_id': employee_id.id or 0,
                'user_name': employee_id.nama_lengkap or "",
                'jabatan': approval.jabatan or "",
                # 'state': approval.action_type or "Waiting Approval",
                'state': dict(approval_model._fields['action_type'].selection).get(approval.action_type) or "Waiting Approval",
                'approve_date': approval.approve_date + timedelta(hours=7) if approval.approve_date else "",
                'notes': approval.notes or "",
                'allow_resend': approval.is_email_sent or False,
            })
    return datas


def get_attachment(leave_id):
    url = request.httprequest.host_url
    image_url = ''
    domain = [('res_field', '=', 'attachment'), ('res_id', '=', leave_id.id), ('res_model', '=', 'hr.leave'), ('company_id', '=', leave_id.mncei_employee_id.company.id)]
    attachment_id = request.env['ir.attachment'].search(domain, limit=1)
    if attachment_id:
        image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(attachment_id.id))
    return image_url


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


def parameter_list(leave_id, state=False):
    leave_model = request.env['hr.leave']
    employee_id = get_employee(leave_id.carteker_id)
    # url = request.httprequest.host_url
    # IUP = request.env['master.bisnis.unit'].sudo().search([('bu_company_id', '=', leave_id.mncei_employee_id.company.id)], limit=1).code
    # image_id = request.env['ir.attachment'].search([
    #     ('name', '=', leave_id.mncei_employee_id.nama_lengkap),
    #     ('company_id', '=', leave_id.mncei_employee_id.company.id),
    #     ('res_field', '=', 'foto_pegawai'),
    #     ('res_id', '=', leave_id.mncei_employee_id.id),
    #     ('res_model', '=', 'hr.leave')
    # ], limit=1)
    # if not image_id:
    #     image_id = add_attachment(leave_id.mncei_employee_id)
    # image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(image_id.id))
    data = {
        'id': leave_id.id or 0,
        'create_date': leave_id.request_date + timedelta(hours=7) if leave_id.request_date else leave_id.create_date + timedelta(hours=7) or "",
        'leave_id': leave_id.holiday_status_id.id or 0,
        'leave_name': leave_id.holiday_status_id.name or "",
        'leave_type': leave_id.holiday_status_id.type_leave or "",
        'holiday_detail_id': leave_id.holiday_detail_id.id or 0,
        'holiday_detail_name': leave_id.holiday_detail_id.name or "",
        'employee_name': leave_id.mncei_employee_id.nama_lengkap or "",
        # 'employee_nik': leave_id.mncei_employee_id.nip_char or "",
        # 'employee_iup': IUP or "",
        # 'employee_jabatan': leave_id.mncei_employee_id.jabatan.name or "",
        # 'employee_image': image_url or "",
        'caretaker_id': employee_id.id or 0,
        'caretaker_name': employee_id.nama_lengkap or "",
        'request_date_from': leave_id.request_date_from or "",
        'request_date_to': leave_id.request_date_to or "",
        'replace_date_from': leave_id.replace_date_from or "",
        'replace_date_to': leave_id.replace_date_to or "",
        'roster_date_from': leave_id.roster_date_from or "",
        'roster_date_to': leave_id.roster_date_to or "",
        'total_days': int(leave_id.number_of_days) or 0,
        'state': dict(leave_model._fields['state'].selection).get(leave_id.state) or "",
        'reason': leave_id.name or "",
        'attachment_name': _("%s - %s") % (leave_id.holiday_status_id.name, leave_id.request_date_from) if get_attachment(leave_id) else "",
        'attachment': get_attachment(leave_id) or "",
        'approval_list': get_approval(leave_id)
    }
    return data


class MncLeave(http.Controller):

    # Master
    @http.route('/api/leave/master/approval_state', type='json', auth="public", csrf=False)
    def getDataApprovalState(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = [
                    {
                        'tech_name': 'Approve',
                        'view_name': 'Approved'
                    },
                    {
                        'tech_name': 'Reject',
                        'view_name': 'Decline'
                    }
                ]

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

    @http.route('/api/leave/master/state', type='json', auth="public", csrf=False)
    def getDataState(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                res_data = [
                    {
                        'tech_name': 'cancel',
                        'view_name': 'Cancel'
                    },
                    {
                        'tech_name': 'confirm',
                        'view_name': 'Waiting Approve'
                    },
                    {
                        'tech_name': 'reject',
                        'view_name': 'Decline'
                    }
                ]

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

    @http.route('/api/leave/master/types', type='json', auth="public", csrf=False)
    def getDataLeaveTypes(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(request.env.user)

                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                domain = []
                if not employee_id.roster_id:
                    domain += [('type_leave', 'not in', ['roster', 'roster_other'])]
                leave_types_ids = request.env['hr.leave.type'].sudo().search(domain)
                for types_id in leave_types_ids:
                    datas = []
                    attachment = False
                    roster = False
                    special_leave = False
                    # By Time Off Officer
                    if types_id.leave_validation_type == 'hr':
                        attachment = True
                    if types_id.type_leave:
                        if types_id.type_leave == 'special_leave':
                            special_leave = True
                            for line in types_id.type_details_ids:
                                datas.append({
                                    'id': line.id,
                                    'name': line.name
                                })
                        if types_id.type_leave == 'roster':
                            roster = True
                    res_data.append({
                        'id': types_id.id,
                        'name': types_id.name,
                        'attachment': attachment,
                        'roster': roster,
                        'special_leave': special_leave,
                        'types': types_id.type_leave,
                        'line': datas
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

    @http.route('/api/leave/user/detail_off', type='json', auth="public", csrf=False)
    def getDataLeaveDetails(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(request.env.user)

                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                datas = {
                    'leave_taken': 0,
                    'leave_total': 0,
                    'carry_over': 0,
                    'mass_leave': 0,
                    'balance': 0,
                }
                # Cuti Bersama Last Year
                get_year = (fields.Datetime.now().year - 1)
                last_start = '%s-01-01' % (get_year)
                last_end = '%s-12-31' % (get_year)
                last_year_domain = [('date_start', '>=', last_start), ('date_end', '<=', last_end), ('state', '=', 'verified'), ('holiday_type', '=', 'mass_leave')]
                last_mass_leave_id = request.env['hr.holidays.public'].sudo().search(last_year_domain, limit=1)
                if last_mass_leave_id:
                    total_mass_leave_last_year = last_mass_leave_id.total_days
                else:
                    total_mass_leave_last_year = 0
                # Cuti Tahunan => Tipe Normal dan Mode Set By Time Officer
                domain_yearly = [('type_leave', '=', 'normal'), ('mnc_allocation_type', '=', 'fixed')]
                holiday_status_id = request.env['hr.leave.type'].sudo().search(domain_yearly, limit=1)
                # In Year
                get_year = (fields.Datetime.now().year)
                start = '%s-01-01' % (get_year)
                end = '%s-12-31' % (get_year)
                total_last_year = 0
                total_in_year = 0
                if holiday_status_id:
                    # =========================================================
                    # Check Leave in Year
                    leave_ids = request.env['hr.leave'].search([('request_date_from', '>=', start), ('request_date_to', '<=', end), ('mncei_employee_id', '=', employee_id.id), ('state', '=', 'validate'), ('holiday_status_id', '=', holiday_status_id.id)])
                    leave_type = holiday_status_id.with_context(mncei_employee_id=employee_id.id)
                    last_leave_type = holiday_status_id.with_context(mncei_employee_id=employee_id.id, last_yearly=True)
                    if leave_ids:
                        for leave_id in leave_ids:
                            calc_duration = leave_id.calculate_days_per_month(leave_id.request_date_from, leave_id.request_date_to)
                            list_values = [i for i in calc_duration.keys()]
                            if len(list_values) > 1:
                                for key in list_values:
                                    if key <= 3:
                                        total_last_year += calc_duration[key]
                                    else:
                                        total_in_year += calc_duration[key]
                            else:
                                if list_values[0] <= 3:
                                    total_last_year += calc_duration[list_values[0]]
                                else:
                                    total_in_year += calc_duration[list_values[0]]
                    # Input Datas
                    datas['leave_taken'] = int(leave_type.leaves_taken)
                    datas['leave_total'] = int(leave_type.max_leaves)
                    datas['carry_over'] = int(last_leave_type.remaining_leaves - total_mass_leave_last_year)
                    # =========================================================
                # Cuti Bersama in Year
                mass_leave_domain = [('date_start', '>=', start), ('date_end', '<=', end), ('state', '=', 'verified'), ('holiday_type', '=', 'mass_leave')]
                mass_leave_id = request.env['hr.holidays.public'].sudo().search(mass_leave_domain, limit=1)
                if mass_leave_id:
                    datas['mass_leave'] = int(mass_leave_id.total_days) if not employee_id.roster_id else 0
                    balance = 0
                    if datas['leave_total'] > 0 or datas['carry_over'] > 0:
                        if employee_id.roster_id:
                            balance = int(abs(datas['leave_total'] + datas['carry_over']) - total_in_year - total_last_year)
                        else:
                            balance = int(abs((datas['leave_total'] + datas['carry_over']) - mass_leave_id.total_days) - total_in_year - total_last_year)
                    datas['balance'] = balance if balance > 0 else 0

                res_data = datas
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

    @http.route('/api/leave/master/caretaker', type='json', auth="public", csrf=False)
    def getDataLeaveCartaker(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(request.env.user)

                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                department_id = employee_id.department
                domain_employee = [('department', '=', department_id.id), ('head_user2', '=', employee_id.head_user2.id), ('id', '!=', employee_id.id)]
                if employee_id.roster_id:
                    domain_employee += [('roster_id', '!=', False)]
                else:
                    domain_employee += [('roster_id', '=', False)]
                employee_ids = request.env['mncei.employee'].sudo().search(domain_employee)
                for caretaker_id in employee_ids:
                    user_id = request.env['res.users'].search([('mncei_employee_id', '=', caretaker_id.id)], limit=1)
                    if user_id:
                        res_data.append({
                            'id': caretaker_id.id,
                            'name': caretaker_id.nama_lengkap,
                            'nip': caretaker_id.nip_char
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

    @http.route('/api/leave/action/edit_draft', type='json', auth="public", csrf=False)
    def EditDraftLeave(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                date_format = "%Y-%m-%d"
                leave_id = request.env['hr.leave'].search([('id', '=', parameter['id']), ('state', '=', 'draft')], limit=1) or False
                if not leave_id:
                    result = {
                        "code": 3,
                        "desc": "ID Not Found",
                        "data": []
                    }
                    return result
                # User Cartaker
                carteker_id = get_cartaker(parameter['caretaker'])

                if not carteker_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Caretaker Not Found, Please Check Related User in Odoo"
                    }
                    return result

                holiday_status_id = request.env['hr.leave.type'].browse(parameter['leave_id'])
                params = {
                    "holiday_status_id": holiday_status_id.id,
                    # "holiday_detail_id": parameter['leave_line_id'],
                    "request_date_from": datetime.strptime(parameter['date_from'], date_format).date(),
                    "request_date_to": datetime.strptime(parameter['date_to'], date_format).date(),
                    "date_from": datetime.strptime(parameter['date_from'], date_format),
                    "date_to": datetime.strptime(parameter['date_to'], date_format),
                    "name": parameter['reason'],
                    "carteker_id": carteker_id.id,
                }
                if parameter['leave_line_id']:
                    params['holiday_detail_id'] = parameter['leave_line_id']
                # Roster
                if parameter['roster_date_from'] and parameter['roster_date_to']:
                    params['roster_date_from'] = datetime.strptime(parameter['roster_date_from'], date_format).date()
                    params['roster_date_to'] = datetime.strptime(parameter['roster_date_to'], date_format).date()
                    params['is_roster'] = True
                    params['is_replace'] = False
                # Replace Date
                if parameter['replace_date_from'] and parameter['replace_date_to']:
                    params['replace_date_from'] = datetime.strptime(parameter['replace_date_from'], date_format).date()
                    params['replace_date_to'] = datetime.strptime(parameter['replace_date_to'], date_format).date()
                    params['is_replace'] = True
                    params['is_roster'] = False

                leave_id.write(params)
                if leave_id.mncei_employee_id.lokasi_kerja.id == 1:
                    days = leave_id._get_number_of_days(leave_id.date_from, leave_id.date_to, 1)['days'] + 1
                    params['number_of_days'] = days
                else:
                    days = (leave_id.date_to - leave_id.date_from).days + 1
                    params['number_of_days'] = days

                res_data.append({'id': leave_id.id})

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

    @http.route('/api/leave/action/set_draft', type='json', auth="public", csrf=False)
    def DraftLeave(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(request.env.user)

                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                # User Cartaker
                carteker_id = get_cartaker(parameter['caretaker'])

                if not carteker_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Caretaker Not Found, Please Check Related User in Odoo"
                    }
                    return result
                if parameter['attachment']:
                    check_image = is_valid_base64(parameter['attachment'])
                    if not check_image:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": "Please check your image"
                        }
                        return result

                leave_id = request.env['hr.leave'].to_create(parameter, carteker_id, code="draft")
                res_data.append({'id': leave_id.id})

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

    @http.route('/api/leave/action/submit', type='json', auth="public", csrf=False)
    def SubmitLeave(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                employee_id = get_employee(request.env.user)

                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                # User Cartaker
                carteker_id = get_cartaker(parameter['caretaker'])

                if not carteker_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "caretaker Not Found, Please Check Related User in Odoo"
                    }
                    return result
                if parameter['attachment']:
                    check_image = is_valid_base64(parameter['attachment'])
                    if not check_image:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": "Please check your image"
                        }
                        return result

                # if not parameter

                leave_id = request.env['hr.leave'].to_create(parameter, carteker_id)
                res_data.append({'id': leave_id.id})

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

    # History
    @http.route('/api/leave/action/approved_list', type='json', auth="public", csrf=False)
    def HistoryApprovedDataLeave(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                # Get Employee
                employee_id = get_employee(request.env.user)
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                # Domain
                domain = []
                if 'all' not in parameter['state']:
                    approval_state = parameter['state']
                elif 'all' in parameter['state']:
                    approval_state = ['Approve', 'Reject']
                # Date Range
                yearly = (fields.Datetime.now().year)
                date_from = '%s-01-01 00:00:00' % (yearly)
                date_to = '%s-12-31 23:59:00' % (yearly)
                # Domain By User
                domain += [('user_approval_ids', 'in', request.env.user.ids), ('create_date', '>=', date_from), ('create_date', '<=', date_to)]
                # Search
                order = _("create_date %s") % (parameter['sort'])
                leave_ids = request.env['hr.leave'].sudo().search(domain, order=order)
                if leave_ids:
                    for leave_id in leave_ids:
                        for line in leave_id.approval_ids.filtered(lambda x: x.action_type in approval_state and x.user_id.id == request.env.user.id):
                            res_data.append(parameter_list(leave_id))

                # ===================================================================================
                # Jumlah total halaman
                page_number = int(request.httprequest.args.get('page'))  # Example page number
                if res_data:
                    # res_data = sorted(res_data, key=lambda x: x['id'])
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

    @http.route('/api/leave/action/waiting_approval', type='json', auth="public", csrf=False)
    def HistoryWaitingDataLeave(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                # Get Employee
                employee_id = get_employee(request.env.user)
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                # Domain
                domain = []
                # if 'all' not in parameter['state']:
                #     domain += [('state', 'in', 'confirm')]
                # Date Range
                yearly = (fields.Datetime.now().year)
                date_from = '%s-01-01 00:00:00' % (yearly)
                date_to = '%s-12-31 23:59:00' % (yearly)
                # Domain By User
                domain += [('approve_uid', '=', request.env.user.id), ('state', '=', 'confirm')]
                # Search
                order = _("create_date %s") % (parameter['sort'])
                leave_ids = request.env['hr.leave'].sudo().search(domain, order=order)
                if leave_ids:
                    for leave_id in leave_ids:
                        res_data.append(parameter_list(leave_id))

                # ===================================================================================
                # Jumlah total halaman
                page_number = int(request.httprequest.args.get('page'))  # Example page number
                if res_data:
                    # res_data = sorted(res_data, key=lambda x: x['id'])
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

    @http.route('/api/leave/action/history', type='json', auth="public", csrf=False)
    def HistoryDataLeave(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                # Get Employee
                employee_id = get_employee(request.env.user)
                if not employee_id:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please create relation user to employee in Odoo"
                    }
                    return result

                # Domain
                domain = []
                if 'all' not in parameter['state']:
                    domain += [('state', 'in', parameter['state'])]
                elif 'all' in parameter['state']:
                    domain += [('state', 'not in', ['draft'])]
                # Date Range
                yearly = (fields.Datetime.now().year)
                date_from = '%s-01-01 00:00:00' % (yearly)
                date_to = '%s-12-31 23:59:00' % (yearly)
                domain += [('mncei_employee_id', '=', employee_id.id), ('create_date', '>=', date_from), ('create_date', '<=', date_to)]
                # Search
                order = _("create_date %s") % (parameter['sort'])
                leave_ids = request.env['hr.leave'].sudo().search(domain, order=order)
                if leave_ids:
                    for leave_id in leave_ids:
                        res_data.append(parameter_list(leave_id))

                # ===================================================================================
                # Jumlah total halaman
                page_number = int(request.httprequest.args.get('page'))  # Example page number
                if res_data:
                    # res_data = sorted(res_data)
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

    @http.route('/api/leave/action/details', type='json', auth="public", csrf=False)
    def getDetails(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            user_id = request.env.user
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                leave_id = search_leave_by_id(parameter['id'])
                if not leave_id:
                    result = {
                        "code": 3,
                        "desc": "ID Not Found",
                        "data": []
                    }
                    return result
                else:
                    if leave_id.approve_uid.id != user_id.id and user_id.id not in leave_id.user_approval_ids.ids and user_id.id != leave_id.user_id.id:
                        result = {
                            "code": 3,
                            "desc": "Your not allowed access",
                            "data": []
                        }
                        return result
                    else:
                        employee_id = leave_id.mncei_employee_id
                        url = request.httprequest.host_url
                        IUP = request.env['master.bisnis.unit'].sudo().search([('bu_company_id', '=', leave_id.mncei_employee_id.company.id)], limit=1).code
                        image_id = request.env['ir.attachment'].search([
                            ('name', '=', leave_id.mncei_employee_id.nama_lengkap),
                            ('company_id', '=', leave_id.mncei_employee_id.company.id),
                            ('res_field', '=', 'foto_pegawai'),
                            ('res_id', '=', leave_id.mncei_employee_id.id),
                            ('res_model', '=', 'hr.leave')
                        ], limit=1)
                        if image_id:
                            image_id.write({
                                'public': True
                            })
                        elif not image_id:
                            image_id = add_attachment(leave_id.mncei_employee_id)
                        image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(image_id.id))
                        employees = {
                            'employee_id': employee_id.id or 0,
                            'employee_nik': employee_id.nip_char or "",
                            'employee_iup': IUP or "",
                            'employee_jabatan': employee_id.jabatan.name or "",
                            'employee_image': image_url or "",
                        }
                        datas_leave = parameter_list(leave_id)
                        merged_dict = {**employees, **datas_leave}
                        res_data.append(merged_dict)

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

    @http.route('/api/leave/action/cancel', type='json', auth="public", csrf=False)
    def CancelRequest(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            # user_id = request.env.user
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                leave_id = request.env['hr.leave'].search([('id', '=', parameter['id']), ('state', '=', 'confirm')], limit=1) or False
                if not leave_id:
                    result = {
                        "code": 3,
                        "desc": "ID Not Found",
                        "data": []
                    }
                    return result

                leave_id.write({'state': 'cancel'})
                # Remove reminder approval
                for line in leave_id.approval_ids:
                    line.write({'is_email_sent': False})

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

    @http.route('/api/leave/action/send_remind', type='json', auth="public", csrf=False)
    def SendNotifyRequest(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            # user_id = request.env.user
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                request_id = request.env['hr.leave.approval'].search([('id', '=', parameter['id'])], limit=1) or False
                if not request_id:
                    result = {
                        "code": 3,
                        "desc": "ID Not Found",
                        "data": []
                    }
                    return result

                # Remind hanya bisa sekali dalam 1 hari
                request_id.write({'is_email_sent': False})
                request_id.send_notify()

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

    @http.route('/api/leave/action/approval', type='json', auth="public", csrf=False)
    def ApprovalLeave(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            user_id = request.env.user
            if key == api_key:
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                leave_id = request.env['hr.leave'].search([('id', '=', parameter['id']), ('state', '=', 'confirm')], limit=1) or False
                if not leave_id:
                    result = {
                        "code": 3,
                        "desc": "ID Not Found",
                        "data": []
                    }
                    return result
                else:
                    if leave_id.approve_uid.id != user_id.id and user_id.id not in leave_id.user_approval_ids.ids and user_id.id != leave_id.user_id.id:
                        result = {
                            "code": 3,
                            "desc": "Your not allowed access",
                            "data": []
                        }
                        return result
                    else:
                        if leave_id.approve_uid.id != user_id.id:
                            result = {
                                "code": 3,
                                "desc": "You're not approval list",
                                "data": []
                            }
                            return result
                        else:
                            # ============== Approve =============
                            approval_id = leave_id.approval_id
                            if parameter['approve'] == 1:
                                next_approver = request.env['hr.leave.approval'].search([
                                    ('id', '>', approval_id.id),
                                    ('leave_id', '=', leave_id.id),
                                ], limit=1, order='id asc')
                                if next_approver:
                                    leave_id.write({'approve_uid': next_approver.user_id.id, 'approval_id': next_approver.id, 'user_approval_ids': [(4, user_id.id)]})
                                    next_approver.write({'is_email_sent': True})
                                else:
                                    leave_id.write({'state': 'validate', 'user_approval_ids': [(4, user_id.id)]})
                                    # If Sick Leave
                                    if leave_id.holiday_status_id.type_leave == 'sick_leave':
                                        # if not attendance_ids:
                                        current_date = leave_id.date_from
                                        while current_date <= leave_id.date_to:
                                            attendance_id = request.env['hr.attendance'].search([('check_in', '=', (current_date - timedelta(hours=7))), ('mncei_employee_id', '=', leave_id.mncei_employee_id.id), ('is_alpha', '=', True)])
                                            if not attendance_id:
                                                att_id = request.env['hr.attendance'].create({
                                                    'mncei_employee_id': leave_id.mncei_employee_id.id,
                                                    'check_in': current_date - timedelta(hours=7),
                                                    'check_out': current_date - timedelta(hours=7),
                                                    'is_sick': True,
                                                    'is_alpha': True,
                                                    'document': leave_id.attachment,
                                                    'document_name': leave_id.filename_attachment,
                                                })
                                            else:
                                                attendance_id.write({
                                                    'is_sick': True,
                                                    'document': leave_id.attachment,
                                                    'document_name': leave_id.filename_attachment,
                                                })
                                            current_date += timedelta(days=1)

                                approval_id.write({
                                    'action_type': 'Approve',
                                    'approve_date': fields.Datetime.now(),
                                    'notes': parameter['notes'],
                                    'is_current_user': True,
                                    'is_email_sent': False,
                                })
                            elif parameter['approve'] == 0:
                                approval_id.write({
                                    'action_type': 'Reject',
                                    'approve_date': fields.Datetime.now(),
                                    'notes': parameter['notes'],
                                    'is_current_user': False,
                                    'is_email_sent': False,
                                })
                                leave_id.write({
                                    'state': 'reject',
                                    'user_approval_ids': [(4, user_id.id)]
                                })
                            result = {
                                "code": 3,
                                "desc": "Success",
                                "data": []
                            }
                            return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
                return result

    @http.route('/api/leave/action/delete', type='json', auth="user", methods=['POST'])
    def DeleteLeaveRequest(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)
            if not parameter['ids']:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": "Please Input Leave ID"
                }
            leave_list = []
            for res_id in parameter['ids']:
                leave_id = search_leave_by_id(res_id)
                if leave_id:
                    leave_id.action_archive()
                else:
                    leave_list.append(res_id)

            if not leave_list:
                return {
                    "code": 2,
                    "desc": "Success",
                    "data": "Leave Success Deleted"
                }
            else:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": _("Leave ID %s Not Found") % (leave_list)
                }
        else:
            result = {"code": 4,
                      "desc": 'Access Denied'}
            return result

    @http.route('/api/leave/action/send_data', type='json', auth="user", methods=['POST'])
    def SendDataLeave(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)
            if not parameter['ids']:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": "Please Input Leave ID"
                }
            leave_list = []
            for res_id in parameter['ids']:
                leave_id = search_leave_by_id(res_id)
                if leave_id:
                    leave_id._search_leave(leave_id.date_from, leave_id.date_to)
                    # ===================================================
                    holiday_detail_id = leave_id.holiday_detail_id.id if leave_id.holiday_detail_id else False
                    leave_id._check_date_request(leave_id.holiday_status_id, fields.Datetime.now(), leave_id.date_from, holiday_detail_id=holiday_detail_id)
                    # ===================================================
                    leave_id.action_submit()
                else:
                    leave_list.append(res_id)

            if not leave_list:
                return {
                    "code": 2,
                    "desc": "Success",
                    "data": "Leave Success Submit"
                }
            else:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": _("Leave ID %s Not Found") % (leave_list)
                }
        else:
            result = {"code": 4,
                      "desc": 'Access Denied'}
            return result
