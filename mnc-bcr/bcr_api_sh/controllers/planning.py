import logging
import werkzeug.wrappers
from datetime import datetime, date
import pytz
import dateutil.parser
from odoo import http, SUPERUSER_ID
from odoo.http import request
import requests
from odoo.tools.safe_eval import safe_eval
import json
import base64

from pytz import utc

try:
    import simplejson as json
except ImportError:
    import json

_logger = logging.getLogger(__name__)

DATETIMEFORMAT = '%Y-%m-%d %H:%M:%S'
DATEFORMAT = '%Y-%m-%d'
LOCALTZ = pytz.timezone('Asia/Jakarta')

class DateEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, date):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def valid_response(status, data):
        return werkzeug.wrappers.Response(
            status=status,
            content_type='application/json; charset=utf-8',
            response=json.dumps(data, cls=DateEncoder),
        )

def default_response(response):
    return {
        "jsonrpc": "2.0",
        "id": False,
        "result": response
    }

def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey

APIKEY = 'e308a8bc-a99e-4cc0-ad7a-cc1c96e7d147'


class BcrInterfacePlanning(http.Controller):

    @http.route('/api/planning/hauling/get', type='json', auth="user", csrf=False)
    def getDataPlanningHauling(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            # if key == APIKEY:
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                datas = values
                domain = []
                vals = []
                # search domain
                if datas:
                    if datas['bisnis_unit_code']:
                        bisnis_unit_id = request.env['master.bisnis.unit'].sudo().search([('code', 'in', datas['bisnis_unit_code'])])
                        # cek data empty
                        if not bisnis_unit_id:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'Bisnis Unit Not Found'}
                            return result
                        else:
                            bu_domain = [dt.bu_company_id.id for dt in bisnis_unit_id]
                            domain += [('bu_company_id', 'in', bu_domain)]

                        if not datas['state']:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'State Not Found'}
                            return result
                        else:
                            domain += [('state', 'in', datas['state'])]

                        if datas['date_start'] and datas['date_end']:
                            domain += [
                                ('date_start', '>=', datas['date_start']),
                                ('date_end', '<=', datas['date_end'])
                            ]

                    hauling_ids = request.env['planning.hauling'].sudo().search(domain)
                    if hauling_ids:
                        for x_data in hauling_ids:
                            obj = {
                                'id': x_data.id or 0,
                                'date_start': x_data.date_start or "0000-00-00",
                                'date_end': x_data.date_end or "0000-00-00",
                                'state': x_data.state or "",
                                'kode': x_data.kode_planning or "",
                                'activity': x_data.activity_id.name or "",
                                'sub_activity_id': x_data.sub_activity_id.id or 0,
                                'sub_activity': x_data.sub_activity_id.name or "",
                                'bisnis_unit_id': x_data.bu_company_id.id or 0,
                                'bisnis_unit_name': x_data.bu_company_id.name or "",
                                'product_id': x_data.product.id or 0,
                                'product': x_data.product.name or "",
                                'workdays': x_data.workdays or 0,
                                'volume_plan': x_data.volume_plan or 0,
                                'revise_note': x_data.revise_note or "",
                                'create_by': x_data.create_uid.name or "",
                                # 'create_date': str(x_data.create_uid.create_date).split(" ")[0] or "0000-00-00",
                                'create_date': str(x_data.create_date).split(" ")[0] or "0000-00-00",
                            }
                            cek_user = x_data.validation_plan.filtered(lambda x: x.user_id.id == request.env.user.id)
                            if request.env.user.tipe_user == "super_admin":
                                vals.append(obj)
                            else:
                                if cek_user:
                                    vals.append(obj)

                    result = {
                        "code": 2,
                        "data": vals,
                        "desc": "Success"
                    }
                    return result

            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/planning/barging/get', type='json', auth="user", csrf=False)
    def getDataPlanningBarging(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            # if key == APIKEY:
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                datas = values
                domain = []
                vals = []
                # search domain
                if datas:
                    if datas['bisnis_unit_code']:
                        bisnis_unit_id = request.env['master.bisnis.unit'].sudo().search(
                            [('code', 'in', datas['bisnis_unit_code'])])
                        # cek data empty
                        if not bisnis_unit_id:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'Bisnis Unit Not Found'}
                            return result
                        else:
                            bu_domain = [dt.bu_company_id.id for dt in bisnis_unit_id]
                            domain += [('bu_company_id', 'in', bu_domain)]

                        if not datas['state']:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'State Not Found'}
                            return result
                        else:
                            domain += [('state', 'in', datas['state'])]

                        if datas['date_start'] and datas['date_end']:
                            domain += [
                                ('date_start', '>=', datas['date_start']),
                                ('date_end', '<=', datas['date_end'])
                            ]

                    barging_ids = request.env['planning.barging'].sudo().search(domain)
                    if barging_ids:
                        for x_data in barging_ids:
                            obj = {
                                    'id': x_data.id or 0,
                                    'date_start': x_data.date_start or "0000-00-00",
                                    'date_end': x_data.date_end or "0000-00-00",
                                    'state': x_data.state or "",
                                    'kode': x_data.kode_planning or "",
                                    'activity': x_data.activity_id.name or "",
                                    'sub_activity_id': x_data.sub_activity_id.id or 0,
                                    'sub_activity': x_data.sub_activity_id.name or "",
                                    'bisnis_unit_id': x_data.bu_company_id.id or 0,
                                    'bisnis_unit_name': x_data.bu_company_id.name or "",
                                    'product_id': x_data.product.id or 0,
                                    'product': x_data.product.name or "",
                                    'workdays': x_data.workdays or 0,
                                    'volume_plan': x_data.volume_plan or 0,
                                    'revise_note': x_data.revise_note or "",
                                    'create_by': x_data.create_uid.name or "",
                                    # 'create_date': str(x_data.create_uid.create_date).split(" ")[0] or "0000-00-00",
                                    'create_date': str(x_data.create_date).split(" ")[0] or "0000-00-00",
                                }
                            cek_user = x_data.validation_plan.filtered(lambda x: x.user_id.id == request.env.user.id)
                            if request.env.user.tipe_user == "super_admin":
                                vals.append(obj)
                            else:
                                if cek_user:
                                    vals.append(obj)



                    result = {
                        "code": 2,
                        "data": vals,
                        "desc": "Success"
                    }
                    return result

            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/planning/production/get', type='json', auth="user", csrf=False)
    def getDataPlanningProduction(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            # if key == APIKEY:
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                datas = values
                domain = []
                vals = []
                # search domain
                if datas:
                    if datas['bisnis_unit_code']:
                        bisnis_unit_id = request.env['master.bisnis.unit'].sudo().search(
                            [('code', 'in', datas['bisnis_unit_code'])])
                        # cek data empty
                        if not bisnis_unit_id:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'Bisnis Unit Not Found'}
                            return result
                        else:
                            bu_domain = [dt.bu_company_id.id for dt in bisnis_unit_id]
                            domain += [('bu_company_id', 'in', bu_domain)]

                        if not datas['state']:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'State Not Found'}
                            return result
                        else:
                            domain += [('state', 'in', datas['state'])]

                        if datas['date_start'] and datas['date_end']:
                            domain += [
                                ('date_start', '>=', datas['date_start']),
                                ('date_end', '<=', datas['date_end'])
                            ]

                    production_ids = request.env['planning.production'].sudo().search(domain)
                    if production_ids:
                        for x_data in production_ids:
                            obj = {
                                'id': x_data.id or 0,
                                'date_start': x_data.date_start or "0000-00-00",
                                'date_end': x_data.date_end or "0000-00-00",
                                'state': x_data.state or "",
                                'kode': x_data.kode_planning or "",
                                'activity': x_data.activity_id.name or "",
                                'sub_activity_id': x_data.sub_activity_id.id or 0,
                                'sub_activity': x_data.sub_activity_id.name or "",
                                'bisnis_unit_id': x_data.bu_company_id.id or 0,
                                'bisnis_unit_name': x_data.bu_company_id.name or "",
                                'kontraktor_id': x_data.kontraktor_id.id or 0,
                                'kontraktor_name': x_data.kontraktor_id.name or "",
                                'area_id': x_data.area_id.id or 0,
                                'area_name': x_data.area_id.name or "",
                                'seam_code_id': x_data.seam_id.id or 0,
                                'seam_code': x_data.seam_id.code or "",
                                'workdays': x_data.workdays or 0,
                                'volume_plan': x_data.volume_plan or 0,
                                'revise_note': x_data.revise_note or "",
                                'create_by': x_data.create_uid.name or "",
                                # 'create_date': str(x_data.create_uid.create_date).split(" ")[0] or "0000-00-00",
                                'create_date': str(x_data.create_date).split(" ")[0] or "0000-00-00",
                            }

                            cek_user = x_data.validation_plan.filtered(lambda x: x.user_id.id == request.env.user.id)
                            if request.env.user.tipe_user == "super_admin":
                                vals.append(obj)
                            else:
                                if cek_user:
                                    vals.append(obj)

                    result = {
                        "code": 2,
                        "data": vals,
                        "desc": "Success"
                    }
                    return result

            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result
