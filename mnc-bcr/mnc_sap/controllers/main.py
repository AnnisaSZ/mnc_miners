import json
from odoo import http, SUPERUSER_ID
from odoo.http import request

from odoo.addons.bcr_api_sh.controllers.main import BcrInterface


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


def get_auto_logout(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('auto_logout')
    return apikey


def get_hazard_company(self):
    sap_company = request.env['ir.config_parameter'].sudo().get_param('sap_company') or []
    return sap_company


class BcrInterface(BcrInterface):

    @http.route('/api/account/detail/get', type='json', auth="user")
    def getDataAccount(self, values=None):
        res = super(BcrInterface, self).getDataAccount(values)

        if res['code'] == 2:
            user = request.env.user
            is_hse = False
            tipe_hse = "User"
            # Check user is group HSE
            if user.has_group('mnc_sap.group_hse'):
                is_hse = True
                tipe_hse = "HSE"
            elif request.env.user.has_group('mnc_sap.group_admin_hse'):
                tipe_hse = "Administrator"

            sap_company = get_hazard_company(self)
            company_hazard = []
            access_hazard = False
            for comp in user.company_ids:
                if str(comp.id) in sap_company:
                    code_comp = request.env['master.bisnis.unit'].sudo().search(
                        [('bu_company_id', '=', comp.id)], limit=1).code
                    if code_comp:
                        company_hazard.append({
                            'id': comp.id,
                            'code': code_comp,
                            'name': comp.name
                        })
                    access_hazard = True

            # Add Values
            res['data']['is_hse'] = is_hse
            res['data']['tipe_hazard'] = tipe_hse or ""
            res['data']['user_companies']['hazard_company'] = company_hazard
            res['data']['access_hazard'] = access_hazard
            res['data']['auto_logout'] = int(get_auto_logout(self)) or 8

        return res


class GetDataSAP(http.Controller):

    @http.route('/api/sap/get/location', type='json', auth="public", csrf=False)
    def getDataLocation(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = [('status', '=', 'aktif')]
                res_data = []

                location_ids = request.env['location.point'].sudo().search(domain)
                for location_id in location_ids:
                    res_data.append({
                        'id': location_id.id,
                        'location': location_id.location,
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

    @http.route('/api/sap/get/activity', type='json', auth="public", csrf=False)
    def getDataActivity(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = [('status', '=', 'aktif')]
                res_data = []

                activity_ids = request.env['activity.hazard'].sudo().search(domain)
                for activity_id in activity_ids:
                    res_data.append({
                        'id': activity_id.id,
                        'activity': activity_id.activity,
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

    @http.route('/api/sap/get/categ_sap', type='json', auth="public", csrf=False)
    def getDataFinding(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = [('status', '=', 'aktif')]
                res_data = []

                categ_sap_ids = request.env['category.hazard'].sudo().search(domain)
                for categ_id in categ_sap_ids:
                    res_data.append({
                        'id': categ_id.id,
                        'code': categ_id.code,
                        'category_sap': categ_id.category,
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

    @http.route('/api/sap/get/category_danger', type='json', auth="public", csrf=False)
    def getDataCategory(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = [('status', '=', 'aktif')]
                res_data = []

                category_ids = request.env['category.danger'].sudo().search(domain)
                for categ_id in category_ids:
                    res_data.append({
                        'id': categ_id.id,
                        'category': categ_id.category_danger,
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

    @http.route('/api/sap/get/department', type='json', auth="public", csrf=False)
    def getDataDepartment(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                # Get Parameter
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result
                # ===================================
                domain = [('status', '=', 'aktif')]
                department_ids = []
                res_data = []

                dept_ids = request.env['department.hse'].sudo().search(domain)
                for dept_id in dept_ids:
                    domain_pic = [('status', '=', 'aktif'), ('company_id', '=', parameter['company_id']), ('department_id', '=', dept_id.id)]
                    pic_ids = request.env['department.pic'].sudo().search(domain_pic)
                    if pic_ids:
                        for pic_id in pic_ids:
                            if pic_id.department_id not in department_ids:
                                department_ids.append(pic_id.department_id)

                if len(department_ids) > 0:
                    for department_id in department_ids:
                        res_data.append({
                            'id': department_id.id,
                            'department': department_id.name,
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

    @http.route('/api/sap/get/pic_department', type='json', auth="public", csrf=False)
    def getDataPICDepartment(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)

                params = values
                domain = [('status', '=', 'aktif'), ('company_id', 'in', request.env.user.company_ids.ids)]
                res_data = []
                print("XXXXXXXXXXXXXXXXX")
                if params['department']:
                    domain.append(('department_id.name', '=', params['department']))

                pic_dept_ids = request.env['department.pic'].sudo().search(domain)
                print(pic_dept_ids)
                for pic_dept in pic_dept_ids:
                    users = []
                    for pic_uid in pic_dept.pic_ids:
                        users.append({
                            'id': pic_uid.id,
                            'name': pic_uid.name,
                        })
                    res_data.append({
                        'id': pic_dept.id,
                        'department': pic_dept.department_id.name,
                        'pic': users
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

    @http.route('/api/sap/get/child_pic', type='json', auth="public", csrf=False)
    def getDataChildPIC(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)

                params = values
                print("====Get Child PIC===")
                print(params)
                domain = [('status', '=', 'aktif'), ('company_id', '=', params['company'])]
                res_data = []
                if params['department']:
                    domain.append(('department_id.id', '=', params['department']))

                pic_dept_ids = request.env['department.pic'].sudo().search(domain)
                for pic_dept in pic_dept_ids:
                    for team_id in pic_dept.child_ids:
                        res_data.append({
                            'id': team_id.id,
                            'user': team_id.child_uid.name,
                            'department': team_id.parent_id.department_id.name
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

    @http.route('/api/sap/get/sanksi', type='json', auth="public", csrf=False)
    def getDataSanksi(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                print("====Get Sanksi===")
                domain = [('status', '=', 'aktif')]
                res_data = []

                penalty_ids = request.env['penalty.point'].sudo().search(domain)
                for penalty_id in penalty_ids:
                    res_data.append({
                        'id': penalty_id.id,
                        'penalty': penalty_id.penalty
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

    @http.route('/api/sap/get/level_resiko', type='json', auth="public", csrf=False)
    def getDataResiko(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                print("====Get Resiko===")
                domain = [('status', '=', 'aktif')]
                res_data = []

                lvl_resiko_ids = request.env['risk.level'].sudo().search(domain)
                for lvl_id in lvl_resiko_ids:
                    res_data.append({
                        'id': lvl_id.id,
                        'level_resiko': lvl_id.risk_level
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

    @http.route('/api/sap/get/risk_control', type='json', auth="public", csrf=False)
    def getDataControlRisk(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = [('status', '=', 'aktif')]
                res_data = []

                control_ids = request.env['risk.control'].sudo().search(domain)
                for control_id in control_ids:
                    res_data.append({
                        'id': control_id.id,
                        'risk_control': control_id.risk_control
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

    @http.route('/api/sap/get/pelaku', type='json', auth="public", csrf=False)
    def getDataPelaku(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                domain = []
                res_data = []
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)

                if parameter['name']:
                    domain = [('name', 'ilike', parameter['name'])]

                user_ids = request.env['res.users'].sudo().search(domain)
                for user_id in user_ids:
                    res_data.append({
                        'id': user_id.id,
                        'name': user_id.name,
                        'email': user_id.login,
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
