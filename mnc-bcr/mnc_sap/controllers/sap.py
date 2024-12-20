import json
import pytz
import base64
import calendar
# import datetime

from odoo import http, SUPERUSER_ID, _
from pytz import UTC
from datetime import datetime, timedelta
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import fields
from .query_reporting import BcrQueryHazard

from dateutil.relativedelta import relativedelta


hazard_state = ["waiting", "hanging", "close", "reject"]

# from mnc_sap.models.mnc_sap import push_notification


def excQueryFetchall(query):
    request.env.cr.execute(query)
    fetch_data = request.env.cr.fetchall()
    return fetch_data


def is_valid_base64(base64_string):
    try:
        base64_bytes = base64.b64decode(base64_string)
        reencoded_base64 = base64.b64encode(base64_bytes)
        return reencoded_base64 == base64_string.encode('utf-8')
    except Exception as e:
        return False


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


def search_sap(sap_no):
    sap_id = request.env['sapform'].search([('sap_no', '=', sap_no)])
    return sap_id


def search_sap_by_id(sap_id):
    sap_id = request.env['sapform'].search([('id', '=', sap_id)])
    return sap_id


def get_attachment(sap_id, fixing=False):
    url = request.httprequest.host_url
    image_url = ''
    domain = [('res_id', '=', sap_id.id), ('res_model', '=', 'sapform'), ('company_id', '=', sap_id.company_id.id)]
    if fixing:
        domain += [('res_field', '=', 'img_eviden_result')]
    else:
        domain += [('res_field', '=', 'img_eviden')]
    attachment_id = request.env['ir.attachment'].search(domain, limit=1)
    attachment_id.public = True
    if attachment_id:
        image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(attachment_id.id))
    return image_url


def parameter_sap_list(sap_id):
    code_comp = request.env['master.bisnis.unit'].sudo().search(
        [('bu_company_id', '=', sap_id.company_id.id)], limit=1).code or ""
    eviden_url = get_attachment(sap_id)
    eviden_result_url = get_attachment(sap_id, fixing=True)
    fixing_date = ""
    if sap_id.fixing_date:
        fixing_date = (sap_id.fixing_date + timedelta(hours=7))
    return {
        'id': sap_id.id,
        'sap_no': sap_id.sap_no,
        'company_code': code_comp,
        'date': sap_id.incident_date_time + timedelta(hours=7),
        'code': sap_id.categ_id.code,
        'report_by': sap_id.create_uid.name,
        'department_report_id': sap_id.report_department_id.id or 0,
        'department_report': sap_id.report_department_id.name or "",
        'company_id': sap_id.company_id.id or 0,
        'company': sap_id.company_id.name,
        'location': sap_id.location_id.location or "",
        'location_id': sap_id.location_id.id or "",
        'detail_location': sap_id.detail_location or "",
        'category_danger': sap_id.danger_categ_id.category_danger or "",
        'category_danger_id': sap_id.danger_categ_id.id or "",
        'lvl_resiko': sap_id.risk_id.risk_level or "",
        'activity_id': sap_id.activity_id.id or 0,
        'activity': sap_id.activity_id.activity or "",
        'department_id': sap_id.department_id.id or 0,
        'department': sap_id.department_id.name or "",
        'pic_department_id': sap_id.pic_id.pic_id.id or 0,
        'pic_department': sap_id.pic_id.pic_id.name or "",
        'risk_control_id': sap_id.control_id.id or 0,
        'risk_control': sap_id.control_id.risk_control or "",
        'description': sap_id.description or "",
        'eviden': "",
        'eviden_url': eviden_url or "",
        'description_result': sap_id.description_result or "",
        'eviden_result': "",
        'eviden_result_url': eviden_result_url or "",
        'self_repair': sap_id.act_repair,
        'state': sap_id.state,
        'act_repair_uid': sap_id.act_repair_uid.id or 0,
        'act_fix_date': fixing_date,
        'act_repair_name': sap_id.act_repair_uid.name or "",
        'is_not_relevan': sap_id.is_not_relevan,
        'is_delegeted': sap_id.is_delegeted,
        'is_hse_receive ': sap_id.is_hse_receive,
    }


class SAP(http.Controller):

    @http.route('/api/sap/hazard/input', type='json', auth="user", methods=['POST'])
    def InputSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                sap_obj = request.env['sapform']
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                if len(parameter) == 0:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please send paramter your input"}
                    return result
                # Check paramater if empty
                time_list = []
                for params in parameter:
                    if params == 'date' or params == 'time':
                        time_list.append(parameter[params])
                date_time = datetime.strptime(' '.join(time_list), "%Y-%m-%d %H:%M:%S") - timedelta(hours=7)
                res_data = []
                # Check Image
                check_image = is_valid_base64(parameter['incident_photo'])
                if not check_image:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please check your image"}
                if parameter['self_repair'] and parameter['code'] not in ('KA', 'TA'):
                    if not parameter['fixing_description']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": "Please input description fixing"}
                        return result
                sap_id = sap_obj.to_create(parameter['code'], parameter, date_time, set_draft=False)
                if sap_id:
                    res_data.append({'sap_id': sap_id.id})
                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please check your data"}
                    return result
            else:
                result = {"code": 4,
                          "desc": 'Access Denied'}
                return result

    @http.route('/api/sap/hazard/set_draft', type='json', auth="user", methods=['POST'])
    def SetDraftSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                sap_obj = request.env['sapform']
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                if len(parameter) == 0:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please send paramter your input"}
                    return result
                # Check paramater if empty
                time_list = []
                for params in parameter:
                    if params == 'date' or params == 'time':
                        time_list.append(parameter[params])
                date_time = datetime.strptime(' '.join(time_list), "%Y-%m-%d %H:%M:%S") - timedelta(hours=7)
                res_data = []
                # Check Image
                check_image = is_valid_base64(parameter['incident_photo'])
                if not check_image:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please check your image generate"}
                sap_id = sap_obj.to_create(parameter['code'], parameter, date_time, set_draft=True)
                if sap_id:
                    res_data.append({'sap_id': sap_id.id})
                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please check your data"}
                    return result
            else:
                result = {"code": 4,
                          "desc": 'Access Denied'}
                return result

    @http.route('/api/sap/hazard/listed', type='json', auth="user", methods=['POST'])
    def ListedSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)
                res_data = []
                company = [('company_id', 'in', request.env.user.company_ids.ids)]
                # Check State
                if 'all' in parameter['state']:
                    domain = [('state', '!=', 'draft')]
                    domain += company
                else:
                    domain = [('state', 'in', parameter['state']), ('company_id', 'in', request.env.user.company_ids.ids)]

                # Check Category
                if 'all' not in parameter['category']:
                    domain += [('sap_type', 'in', parameter['category'])]
                # Check User Groups
                # HSE Groups
                if request.env.user.has_group('mnc_sap.group_hse'):
                    if "draft" in parameter['state']:
                        domain += [('create_uid', '=', request.env.user.id)]
                # User Not HSE
                else:
                    if len(parameter['state']) == 2:
                        domain += ['|', ('pic_uids', 'in', request.env.user.ids), ('child_pic.child_uid', 'in', request.env.user.ids)]
                    elif "draft" in parameter['state']:
                        domain += [('create_uid', '=', request.env.user.id)]
                    else:
                        domain += [('create_uid', '=', request.env.user.id)]

                # Check Order By
                if len(parameter['state']) == 2:
                    order = _("incident_date_time %s") % (parameter['sort'])
                elif "draft" in parameter['state']:
                    order = _("incident_date_time %s") % (parameter['sort'])
                else:
                    order = _("seq_number %s") % (parameter['sort'])
                # Range Date
                if parameter['month'] > 0 and parameter['month'] < 13 and "draft" not in parameter['state']:
                    start_date = datetime(parameter['year'], parameter['month'], 1)
                    end_date = (start_date.replace(day=1) + relativedelta(months=1, days=-1)) + timedelta(days=1)
                    domain += [('incident_date_time', '>=', start_date), ('incident_date_time', '<=', end_date)]
                # Search Hazard Report
                sap_ids = request.env['sapform'].sudo().search(domain, order=order)
                for sap_id in sap_ids:
                    if request.env.user.has_group('mnc_sap.group_hse'):
                        if sap_id.create_uid != request.env.user and sap_id.state != 'draft':
                            res_data.append(parameter_sap_list(sap_id))
                        else:
                            res_data.append(parameter_sap_list(sap_id))
                    else:
                        res_data.append(parameter_sap_list(sap_id))
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

    @http.route('/api/sap/hazard/table/reporting', type='json', auth="user", methods=['GET'])
    def GetReportingSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)
                res_data = []
                user_id = request.env.user.id
                if parameter['month'] > 0 and parameter['month'] < 13:
                    start_date = datetime(parameter['year'], parameter['month'], 1)
                    end_date = (start_date.replace(day=1) + relativedelta(months=1, days=-1)) + timedelta(days=1)
                # Get Query
                get_datas = excQueryFetchall(BcrQueryHazard.QueryTableReport(self, user_id, start_date, end_date))
                # Add Data
                data_state = []
                if get_datas:
                    for data in get_datas:
                        data_state.append(data[0])
                        res_data.append({
                            'state': data[0],
                            'KTA': data[1],
                            'TTA': data[2],
                            'KA': data[3],
                            'TA': data[4],
                        })
                    # Check State and Update State if not in Datas
                    for st in hazard_state:
                        if st not in data_state:
                            res_data.append({
                                'state': st,
                                'KTA': 0,
                                'TTA': 0,
                                'KA': 0,
                                'TA': 0,
                            })
                else:
                    for st in hazard_state:
                        res_data.append({
                            'state': st,
                            'KTA': 0,
                            'TTA': 0,
                            'KA': 0,
                            'TA': 0,
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
        else:
            result = {
                "code": 4,
                "desc": 'Access Denied'
            }
            return result

    @http.route('/api/sap/hazard/table/fixing', type='json', auth="user", methods=['GET'])
    def GetFixingSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)
                res_data = []
                user_id = request.env.user.id
                if parameter['month'] > 0 and parameter['month'] < 13:
                    start_date = datetime(parameter['year'], parameter['month'], 1)
                    end_date = (start_date.replace(day=1) + relativedelta(months=1, days=-1)) + timedelta(days=1)
                # Get Query
                get_datas = excQueryFetchall(BcrQueryHazard.QueryTableFixing(self, user_id, start_date, end_date))
                if get_datas:
                    for data in get_datas:
                        res_data.append({
                            'state': data[0],
                            'KTA': data[1],
                            'TTA': data[2],
                            'KA': data[3],
                            'TA': data[4],
                        })
                else:
                    res_data.append({
                        'state': "close",
                        'KTA': 0,
                        'TTA': 0,
                        'KA': 0,
                        'TA': 0,
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
        else:
            result = {
                "code": 4,
                "desc": 'Access Denied'
            }
            return result

    @http.route('/api/sap/hazard/edit', type='json', auth="user", methods=['POST'])
    def EditSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)

            if not parameter['sap_id']:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": "Please Input SAP No"
                }
            sap_id = search_sap_by_id(parameter['sap_id'])
            time_list = []
            for params in parameter:
                if params == 'date' or params == 'time':
                    time_list.append(parameter[params])
            date_time = datetime.strptime(' '.join(time_list), "%Y-%m-%d %H:%M:%S") - timedelta(hours=7)
            if sap_id and sap_id.state == 'draft':
                prepare_data = {
                    "company_id": parameter['company'],
                    "incident_date_time": date_time,
                    "location_id": parameter['location'],
                    "detail_location": parameter['detail_location'] or "",
                    "risk_id": parameter['risk_level'] or False,
                    "control_id": parameter['control_id'] or False,
                    "danger_categ_id": parameter['category'] or False,
                    "activity_id": parameter['activity'] or False,
                    "description": parameter['incident_description'],
                    "img_eviden": parameter['incident_photo'],
                    "description_result": parameter['fixing_description'] or False,
                    "img_eviden_result": parameter['fixing_photo'] or False,
                }
                sap_id.write(prepare_data)
                result = {
                    "code": 2,
                    "desc": "Success",
                    "data": sap_id.id
                }
                return result
            else:
                result = {
                    "code": 3,
                    "desc": 'SAP Not Found'
                }
                return result
        else:
            result = {
                "code": 4,
                "desc": 'Access Denied'
            }
            return result

    @http.route('/api/sap/hazard/delete', type='json', auth="user", methods=['POST'])
    def DeleteSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)
            if not parameter['sap_id']:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": "Please Input SAP ID"
                }
            sap_list = []
            for sap_id in parameter['sap_id']:
                sap = search_sap_by_id(sap_id)
                if sap:
                    sap.action_archive()
                else:
                    sap_list.append(sap_id)

            if not sap_list:
                return {
                    "code": 2,
                    "desc": "Success",
                    "data": "SAP Success Deleted"
                }
            else:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": _("SAP ID %s Not Found") % (sap_list)
                }
        else:
            result = {"code": 4,
                      "desc": 'Access Denied'}
            return result

    @http.route('/api/sap/hazard/submit', type='json', auth="user", methods=['POST'])
    def SubmitSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)
            if not parameter['sap_id']:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": "Please Input SAP ID"
                }
            sap = search_sap_by_id(parameter['sap_id'])
            if sap:
                if sap.state == 'close':
                    return {
                        "code": 3,
                        "desc": "Failed",
                        "data": "SAP is Complete"
                    }
                if sap.state == 'draft':
                    sap.check_date_lock_incident()
                # Complete or Close Report
                if parameter['code'] == 1:
                    if sap.state == 'draft':
                        sap.write({
                            'sap_no': sap.sap_type + '/' + sap.get_sequence(),
                        })
                    risk_control_id = False
                    control_id = request.env['risk.control'].browse(parameter['risk_control_id'])
                    if control_id:
                        risk_control_id = control_id.id
                    sap.write({
                        'description_result': parameter['fixing_description'],
                        'img_eviden_result': parameter['fixing_photo'],
                        'act_repair_uid': request.env.user.id,
                        'fixing_date': fields.Datetime.now(),
                        'control_id': risk_control_id,
                        'is_not_relevan': False,
                        'state': 'close'
                    })
                    # ========== Notification ===========
                    # To Reporter
                    user = sap.create_uid
                    if sap.act_repair_uid != sap.create_uid:
                        sap.send_notification(user, "HSE-04", sap)
                    # To HSE
                    hse_department_id = request.env['department.pic'].search([('department_id.name', 'like', 'HSE'), ('status', '=', 'aktif'), ('company_id', '=', sap.company_id.id)], limit=1)
                    if hse_department_id:
                        for user_department in hse_department_id.pic_ids:
                            user = user_department
                            sap.send_notification(user, "HSE-05", sap)
                    # To PIC
                    if sap.pic_id:
                        for user_pic in sap.pic_id.pic_ids:
                            sap.send_notification(user_pic, "HSE-04", sap)
                    return {
                        "code": 2,
                        "desc": "Success",
                        "data": "SAP is closed"
                    }
                # ========== //////////// ===========
                # Send and to waiting, if department
                else:
                    sap.write({
                        'sap_no': sap.sap_type + '/' + sap.get_sequence(),
                        'department_id': parameter['department'],
                    })
                    result = sap.action_to_waiting(parameter['department'])
                    if result:
                        # Notif To HSE
                        # hse_department_id = request.env['department.pic'].search([('department_id.name', 'like', 'HSE'), ('status', '=', 'aktif'), ('company_id', '=', sap.company_id.id)], limit=1)
                        # if hse_department_id:
                        #     for user_department in hse_department_id.pic_ids:
                        #         user = user_department
                        #         sap.send_notification(user, "HSE-05", sap)
                        return {
                            "code": 2,
                            "desc": "Success",
                            "data": "SAP Success Submit"
                        }
                    else:
                        return {
                            "code": 3,
                            "desc": "Failed",
                            "data": "PIC Not Found in Your Company"
                        }
            else:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": "SAP Not Found"
                }
        else:
            result = {"code": 4,
                      "desc": 'Access Denied'}
            return result

    # API untuk melakukan not relevan dan send delegeted(bawahan)
    @http.route('/api/sap/hazard/revise', type='json', auth="user", methods=['POST'])
    def ReviseSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)

            if not parameter['sap_id']:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": "Please Input SAP ID"
                }
            sap_id = search_sap_by_id(parameter['sap_id'])
            if sap_id:
                # Code 1 (not relevant department)
                if parameter['code'] == 1:
                    if request.env.user.has_group('mnc_sap.group_hse') or request.env.user.id in sap_id.pic_id.pic_ids.ids:
                        success = sap_id.not_relevan_report(parameter)
                        if success:
                            return {
                                "code": 2,
                                "desc": "Success",
                                "data": "SAP To Hanging"
                            }
                        else:
                            return {
                                "code": 3,
                                "desc": "Failed",
                                "data": "Dept HSE not configuration"
                            }
                    elif request.env.user.id not in sap_id.pic_id.pic_ids.ids:
                        return {
                            "code": 3,
                            "desc": "Failed",
                            "data": "Your not PIC or HSE"
                        }
                # Code 2 (delegated teams)
                elif parameter['code'] == 2:
                    sap_id.write({
                        'child_pic': parameter['delegated'],
                        'is_delegeted': True,
                        'state': 'hanging'
                    })
                    # Send To user fixing
                    user = sap_id.child_pic.child_uid
                    sap_id.send_notification(user, "HSE-11", sap_id)
                    return {
                        "code": 2,
                        "desc": "Success",
                        "data": "Delegated Success"
                    }
                # Change PIC after not relevan
                elif parameter['code'] == 3:
                    sap_id.write({
                        'department_id': parameter['department'],
                        # 'is_not_relevan': True
                    })
                    result = sap_id.action_to_waiting(parameter['department'])
                    if result:
                        return {
                            "code": 2,
                            "desc": "Success",
                            "data": "Change PIC Success"
                        }
                    else:
                        return {
                            "code": 3,
                            "desc": "Failed",
                            "data": "PIC Not Found in Your Company"
                        }
                else:
                    result = {
                        "code": 3,
                        "desc": 'Code Not Found'}
                    return result
            else:
                result = {
                    "code": 3,
                    "desc": 'Request Failed'}
                return result
        else:
            result = {"code": 4,
                      "desc": 'Access Denied'}
            return result

    @http.route('/api/sap/hazard/reject', type='json', auth="user", methods=['POST'])
    def RejectSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)

            if not parameter['sap_id']:
                return {
                    "code": 3,
                    "desc": "Failed",
                    "data": "Please Input SAP ID"
                }
            sap_id = search_sap_by_id(parameter['sap_id'])
            groups = request.env.ref('mnc_sap.group_hse')
            if sap_id and sap_id.state in ('hanging', 'waiting') and request.env.user.id in groups.users.ids:
                # to reporter
                sap_id.send_notification(sap_id.create_uid, "HSE-08", sap_id)
                if sap_id.state == 'waiting':
                    # To PIC
                    for user in sap_id.pic_id.pic_ids:
                        sap_id.send_notification(user, "HSE-07", sap_id)
                sap_id.write({
                    'state': 'reject',
                    'reject_uid': request.env.user.id
                })
                return {
                    "code": 2,
                    "desc": "Success",
                    "data": "Rejected Success"
                }
            else:
                result = {
                    "code": 3,
                    "desc": 'Request Failed'}
                return result
        else:
            result = {"code": 4,
                      "desc": 'Access Denied'}
            return result

    @http.route('/api/sap/hazard/details', type='json', auth="user", methods=['GET'])
    def DetailSAP(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                parameter = json.loads(request.httprequest.data)
                # To Get Datas
                res_data = []
                if not parameter['sap_id']:
                    return {
                        "code": 3,
                        "desc": "Failed",
                        "data": "Please Input SAP ID"
                    }
                sap_id = search_sap_by_id(parameter['sap_id'])
                if sap_id:
                    res_data.append(parameter_sap_list(sap_id))
                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "desc": "SAP Cann't Found"}
                    return result
            else:
                result = {
                    "code": 3,
                    "desc": 'Access Denied'}
                return result
        else:
            result = {"code": 4,
                      "desc": 'Access Denied'}
            return result
