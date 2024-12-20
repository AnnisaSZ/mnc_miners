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

class BcrInterfacePlanningRevise(http.Controller):

    @http.route('/api/planning/hauling/revise', type='json', auth="public", csrf=False)
    def getDataPlanningHaulingRevise(self, values=None):
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
                    if not datas['id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Id Not Found'}
                        return result
                    else:
                        domain += [('id', '=', datas['id'])]

                    if not datas['note']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Fill Revise Note before click Revise'}
                        return result

                    desc = ""
                    code = 0
                    hauling_data = request.env['planning.hauling'].sudo().search(domain)
                    if hauling_data:
                        hauling_data.write(
                            {
                                "state": "review",
                                "revise_note": datas['note'],
                            }
                        )
                        vals.append({
                            'id': hauling_data.id,
                            'kode': hauling_data.kode_planning
                        })
                        code = 2
                        desc = "Success"

                    else:
                        vals.append({
                            'id': datas['id']
                        })
                        code = 3
                        desc = "Failed"

                    result = {
                        "code": code,
                        "data": vals,
                        "desc": desc
                    }
                    return result

            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/planning/barging/revise', type='json', auth="public", csrf=False)
    def getDataPlanningBargingRevise(self, values=None):
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
                    if not datas['id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Id Not Found'}
                        return result
                    else:
                        domain += [('id', '=', datas['id'])]

                    if not datas['note']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Fill Revise Note before click Revise'}
                        return result

                    desc = ""
                    code = 0
                    barging_data = request.env['planning.barging'].sudo().search(domain)
                    if barging_data:
                        barging_data.write(
                            {
                                "state": "review",
                                "revise_note": datas['note'],
                            }
                        )
                        vals.append({
                            'id': barging_data.id,
                            'kode': barging_data.kode_planning
                        })
                        code = 2
                        desc = "Success"

                    else:
                        vals.append({
                            'id': datas['id']
                        })
                        code = 3
                        desc = "Failed"

                    result = {
                        "code": code,
                        "data": vals,
                        "desc": desc
                    }
                    return result

            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/planning/production/revise', type='json', auth="public", csrf=False)
    def getDataPlanningProductionRevise(self, values=None):
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
                    if not datas['id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Id Not Found'}
                        return result
                    else:
                        domain += [('id', '=', datas['id'])]

                    if not datas['note']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Fill Revise Note before click Revise'}
                        return result

                    desc = ""
                    code = 0
                    production_data = request.env['planning.production'].sudo().search(domain)
                    if production_data:
                        production_data.write(
                            {
                                "state": "review",
                                "revise_note": datas['note'],
                            }
                        )
                        vals.append({
                            'id': production_data.id,
                            'kode': production_data.kode_planning
                        })
                        code = 2
                        desc = "Success"

                    else:
                        vals.append({
                            'id': datas['id']
                        })
                        code = 3
                        desc = "Failed"

                    result = {
                        "code": code,
                        "data": vals,
                        "desc": desc
                    }
                    return result

            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result
