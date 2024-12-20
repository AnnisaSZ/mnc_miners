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

from .date_lock_act import BcrDateLock

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


class BcrInterfaceActApprove(http.Controller):
    @http.route('/api/act/hauling/approve', type='json', auth="public", csrf=False)
    def getDataActHaulingApprove(self, values=None):
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

                    desc = ""
                    code = 0
                    hauling_data = request.env['act.hauling'].sudo().search(domain)
                    if hauling_data:
                        if BcrDateLock.cek_date_lock_act(self, "approve", request.env.user.id, hauling_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "approve")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result

                        hauling_data.write(
                            {"state": "complete"}
                        )
                        vals.append({
                            'id': hauling_data.id,
                            'kode': hauling_data.kode
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

    @http.route('/api/act/barging/approve', type='json', auth="public", csrf=False)
    def getDataActBargingApprove(self, values=None):
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

                    desc = ""
                    code = 0
                    barging_data = request.env['act.barging'].sudo().search(domain)
                    if barging_data:
                        if BcrDateLock.cek_date_lock_act(self, "approve", request.env.user.id, barging_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "approve")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result

                        barging_data.write(
                            {"state": "complete"}
                        )
                        vals.append({
                            'id': barging_data.id,
                            'kode': barging_data.kode
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

    @http.route('/api/act/production/approve', type='json', auth="public", csrf=False)
    def getDataActProductionApprove(self, values=None):
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

                    desc = ""
                    code = 0
                    production_data = request.env['act.production'].sudo().search(domain)
                    if production_data:
                        if BcrDateLock.cek_date_lock_act(self, "approve", request.env.user.id, production_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "approve")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result

                        production_data.write(
                            {"state": "complete"}
                        )
                        vals.append({
                            'id': production_data.id,
                            'kode': production_data.kode
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

    @http.route('/api/act/inventory/approve', type='json', auth="public", csrf=False)
    def getDataActInventoryApprove(self, values=None):
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

                    desc = ""
                    code = 0
                    stockroom_data = request.env['act.stockroom'].sudo().search(domain)
                    if stockroom_data:
                        if BcrDateLock.cek_date_lock_act(self, "approve", request.env.user.id, stockroom_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "approve")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result

                        stockroom_data.write(
                            {"state": "complete"}
                        )
                        vals.append({
                            'id': stockroom_data.id,
                            'kode': stockroom_data.kode
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

    @http.route('/api/act/delay/approve', type='json', auth="public", csrf=False)
    def getDataActDelayApprove(self, values=None):
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

                    desc = ""
                    code = 0
                    delay_data = request.env['act.delay'].sudo().search(domain)
                    if delay_data:
                        if BcrDateLock.cek_date_lock_act(self, "approve", request.env.user.id, delay_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "approve")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result

                        delay_data.write(
                            {"state": "complete"}
                        )
                        vals.append({
                            'id': delay_data.id,
                            'kode': delay_data.kode
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
