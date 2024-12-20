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

from .notification import BcrInterfaceNotification

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


class BcrInterfacePlanningReview(http.Controller):
    @http.route('/api/planning/hauling/review', type='json', auth="public", csrf=False)
    def getDataPlanningHaulingReview(self, values=None):
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

                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['sub_activity_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Id Not Found'}
                        return result

                    if not datas['product_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Product Id Not Found'}
                        return result

                    if not datas['volume_plan']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Volume Not Found'}
                        return result

                    if not datas['tipe_review']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tipe Review Not Found'}
                        return result

                    desc = ""
                    code = 0
                    hauling_data = request.env['planning.hauling'].sudo().search(domain)
                    if hauling_data:
                        # 2 untuk merubah state review
                        if datas['tipe_review'] == 2:
                            hauling_data.write(
                                {
                                    "state": "approve",
                                    "date_start": datas['date_start'],
                                    "date_end": datas['date_end'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "volume_plan": datas['volume_plan']
                                 }
                            )
                        else:
                            hauling_data.write(
                                {
                                    "date_start": datas['date_start'],
                                    "date_end": datas['date_end'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "volume_plan": datas['volume_plan']
                                }
                            )

                        vals.append({
                            'id': hauling_data.id,
                            'kode': hauling_data.kode_planning,
                            'date_start':  datas['date_start'],
                            'date_end': datas['date_end'],
                            'sub_activity_id': datas['sub_activity_id'],
                            'product': datas['product_id'],
                            'volume_plan': datas['volume_plan']
                        })
                        code = 2
                        desc = "Success"

                        src_usr_val = BcrInterfaceNotification.search_usr_validation_by_model(self,
                            "validation_planning_hauling_id", datas['id'], "approve")
                        if src_usr_val:
                            for user in src_usr_val:
                                request.env['push.notification'].sudo().push_notification_person(user.user_id.login, "planning.hauling", "approve", hauling_data.kode_planning)

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

    @http.route('/api/planning/barging/review', type='json', auth="public", csrf=False)
    def getDataPlanningBargingReview(self, values=None):
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

                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['sub_activity_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Id Not Found'}
                        return result

                    if not datas['product_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Product Id Not Found'}
                        return result

                    if not datas['volume_plan']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Volume Not Found'}
                        return result

                    if not datas['tipe_review']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tipe Review Not Found'}
                        return result

                    desc = ""
                    code = 0
                    barging_data = request.env['planning.barging'].sudo().search(domain)
                    if barging_data:
                        # 2 untuk merubah state review
                        if datas['tipe_review'] == 2:
                            barging_data.write(
                                {
                                    "state": "approve",
                                    "date_start": datas['date_start'],
                                    "date_end": datas['date_end'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "volume_plan": datas['volume_plan']
                                }
                            )
                        else:
                            barging_data.write(
                                {
                                    "date_start": datas['date_start'],
                                    "date_end": datas['date_end'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "volume_plan": datas['volume_plan']
                                }
                            )
                        vals.append({
                            'id': barging_data.id,
                            'kode': barging_data.kode_planning,
                            'date_start': datas['date_start'],
                            'date_end': datas['date_end'],
                            'sub_activity_id': datas['sub_activity_id'],
                            'product': datas['product_id'],
                            'volume_plan': datas['volume_plan']
                        })
                        code = 2
                        desc = "Success"

                        src_usr_val = BcrInterfaceNotification.search_usr_validation_by_model(self,"validation_planning_barging_id",datas['id'], "approve")
                        if src_usr_val:
                            for user in src_usr_val:
                                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"planning.barging","approve",barging_data.kode_planning)

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



    @http.route('/api/planning/production/review', type='json', auth="public", csrf=False)
    def getDataPlanningProductionReview(self, values=None):
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

                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['sub_activity_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Id Not Found'}
                        return result

                    if not datas['area_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Area Id Not Found'}
                        return result

                    if not datas['kontraktor_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Kontraktor Id Not Found'}
                        return result

                    if not datas['volume_plan']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Volume Not Found'}
                        return result

                    if not datas['tipe_review']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tipe Review Not Found'}
                        return result

                    desc = ""
                    code = 0
                    production_data = request.env['planning.production'].sudo().search(domain)
                    if production_data:
                        # 2 untuk merubah state review
                        if datas['tipe_review'] == 2:
                            production_data.write(
                                {
                                    "state": "approve",
                                    "date_start": datas['date_start'],
                                    "date_end": datas['date_end'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "area_id": datas['area_id'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "volume_plan": datas['volume_plan']
                                }
                            )
                        else:
                            production_data.write(
                                {
                                    "date_start": datas['date_start'],
                                    "date_end": datas['date_end'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "area_id": datas['area_id'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "volume_plan": datas['volume_plan']
                                }
                            )
                        vals.append({
                            'id': production_data.id,
                            'kode': production_data.kode_planning,
                            'date_start': datas['date_start'],
                            'date_end': datas['date_end'],
                            'sub_activity_id': datas['sub_activity_id'],
                            'area_id': datas['area_id'],
                            'kontraktor_id': datas['kontraktor_id'],
                            'volume_plan': datas['volume_plan']
                        })
                        code = 2
                        desc = "Success"

                        src_usr_val = BcrInterfaceNotification.search_usr_validation_by_model(self,"validation_planning_production_id",datas['id'], "approve")
                        if src_usr_val:
                            for user in src_usr_val:
                                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"planning.production","approve",production_data.kode_planning)

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
