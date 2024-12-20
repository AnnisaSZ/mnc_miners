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
from odoo import api, fields, models, tools
from .query_dashboard import BcrQeuryResume,BcrQeuryInventoryUpdate,BcrQeuryRangkingKontraktor,\
    BcrQeuryRangkingBU,BcrQeuryBestAchivement,BcrQeuryJettyActivity,BcrQeuryShippingUpdate,\
    BcrQeuryProductTrend,BcrQeuryRealtimeCoalbyWeighbridge

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


def excQueryFetchall(query):
    request.env.cr.execute(query)
    fetch_data = request.env.cr.fetchall()
    return fetch_data


class BcrInterfaceDashboard(http.Controller):

    @http.route('/api/dashboard/od/table/overview', type='json', auth="public", csrf=False)
    def getDataDashTblOverview(self, values=None):
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

                if datas:
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(BcrQeuryResume.QueryTableOverview(self, datas['date'], datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'item': data[0] or 0,
                            'overburden': data[1] or 0,
                            'coal_getting': data[2] or 0,
                            'sr': data[3] or 0,
                            'rain_slippery': data[4] or 0,
                            'coal_hauling': data[5] or 0,
                            'coal_barging': data[6] or 0
                        })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/od/cg/mtd', type='json', auth="public", csrf=False)
    def getDataDashCGMTD(self, values=None):
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

                if datas:
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(BcrQeuryResume.QueryCGMTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "AKTUAL MTD":
                        actual_mtd = data[1]
                    if data[0] == "PLAN MTD":
                        plan_mtd = data[1]
                    if data[0] == "PLAN EOM":
                        plan_eom = data[1]
                    if data[0] == "PLAN SR":
                        sr_plan = data[1]
                    if data[0] == "AKTUAL SR":
                        sr_actual = data[1]

                if ex_data:
                    vals.append({
                        'actual_mtd': actual_mtd or 0,
                        'plan_mtd': plan_mtd or 0,
                        'plan_eom': plan_eom or 0,
                        'sr_plan': sr_plan or 0,
                        'sr_actual': sr_actual or 0
                    })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/od/cg/ytd', type='json', auth="public", csrf=False)
    def getDataDashCGYTD(self, values=None):
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
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                ex_data = excQueryFetchall(BcrQeuryResume.QueryCGYTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "AKTUAL YTD":
                        actual_ytd = data[1]
                    if data[0] == "PLAN YTD":
                        plan_ytd = data[1]
                    if data[0] == "PLAN EOY":
                        plan_eoy = data[1]
                    if data[0] == "PLAN SR":
                        sr_plan = data[1]
                    if data[0] == "AKTUAL SR":
                        sr_actual = data[1]

                if ex_data:
                    vals.append({
                        'actual_ytd': actual_ytd or 0,
                        'plan_ytd': plan_ytd or 0,
                        'plan_eoy': plan_eoy or 0,
                        'sr_plan': sr_plan or 0,
                        'sr_actual': sr_actual or 0
                    })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/od/overburden/mtd', type='json', auth="public", csrf=False)
    def getDataDashOverburdenMTD(self, values=None):
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
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                ex_data = excQueryFetchall(BcrQeuryResume.QueryOBMTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "AKTUAL MTD":
                        actual_mtd = data[1]
                    if data[0] == "PLAN MTD":
                        plan_mtd = data[1]
                    if data[0] == "PLAN EOM":
                        plan_eom = data[1]
                if ex_data:
                    vals.append({
                        'actual_mtd': actual_mtd or 0,
                        'plan_mtd': plan_mtd or 0,
                        'plan_eom': plan_eom or 0
                    })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/od/overburden/ytd', type='json', auth="public", csrf=False)
    def getDataDashOverburdenYTD(self, values=None):
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
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                ex_data = excQueryFetchall(BcrQeuryResume.QueryOBYTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "AKTUAL YTD":
                        actual_ytd = data[1]
                    if data[0] == "PLAN YTD":
                        plan_ytd = data[1]
                    if data[0] == "PLAN EOY":
                        plan_eoy = data[1]
                if ex_data:
                    vals.append({
                        'actual_ytd': actual_ytd or 0,
                        'plan_ytd': plan_ytd or 0,
                        'plan_eoy': plan_eoy or 0
                    })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/od/hauling/mtd', type='json', auth="public", csrf=False)
    def getDataDashHaulingMTD(self, values=None):
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
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                ex_data = excQueryFetchall(BcrQeuryResume.QueryHaulingMTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "AKTUAL MTD":
                        actual_mtd = data[1]
                    if data[0] == "PLAN MTD":
                        plan_mtd = data[1]
                    if data[0] == "PLAN EOM":
                        plan_eom = data[1]
                if ex_data:
                    vals.append({
                        'actual_mtd': actual_mtd or 0,
                        'plan_mtd': plan_mtd or 0,
                        'plan_eom': plan_eom or 0
                    })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/od/hauling/ytd', type='json', auth="public", csrf=False)
    def getDataDashSRYTD(self, values=None):
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
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                ex_data = excQueryFetchall(BcrQeuryResume.QueryHaulingYTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "AKTUAL YTD":
                        actual_ytd = data[1]
                    if data[0] == "PLAN YTD":
                        plan_ytd = data[1]
                    if data[0] == "PLAN EOY":
                        plan_eoy = data[1]
                if ex_data:
                    vals.append({
                        'actual_ytd': actual_ytd or 0,
                        'plan_ytd': plan_ytd or 0,
                        'plan_eoy': plan_eoy or 0
                    })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/od/cb/mtd', type='json', auth="public", csrf=False)
    def getDataDashCBMTD(self, values=None):
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
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                ex_data = excQueryFetchall(BcrQeuryResume.QueryBargingMTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "PLAN MTD":
                        plan_mtd = data[1]
                    if data[0] == "ACTUAL MTD":
                        actual_mtd = data[1]
                    if data[0] == "PLAN EOM":
                        plan_eom = data[1]
                if ex_data:
                    vals.append({
                        'plan_mtd': plan_mtd or 0,
                        'actual_mtd': actual_mtd or 0,
                        'plan_eom': plan_eom or 0
                    })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/od/cb/ytd', type='json', auth="public", csrf=False)
    def getDataDashCBYTD(self, values=None):
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
                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                ex_data = excQueryFetchall(BcrQeuryResume.QueryBargingYTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "ACTUAL YTD":
                        actual_ytd = data[1]
                    if data[0] == "PLAN YTD":
                        plan_ytd = data[1]
                    if data[0] == "PLAN EOY":
                        plan_eoy = data[1]
                if ex_data:
                    vals.append({
                        'actual_ytd': actual_ytd or 0,
                        'plan_ytd': plan_ytd or 0,
                        'plan_eoy': plan_eoy or 0
                    })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    # inventory
    @http.route('/api/dashboard/iu/sub_activity', type='json', auth="public", csrf=False)
    def getDataDashIUSubActivity(self, values=None):
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

                if datas:
                    # if not datas['date']:
                    #     result = {
                    #         "code": 3,
                    #         "data": [],
                    #         "desc": 'Date Not Found'}
                    #     return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(BcrQeuryInventoryUpdate.QueryIUSubActivity(self, datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'sub_activity': data[0] or 0,
                            'last_updated': data[1] or 0,
                            'volume': data[2] or 0
                        })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/iu/iup', type='json', auth="public", csrf=False)
    def getDataDashIUIUP(self, values=None):
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

                if datas:
                    # if not datas['date']:
                    #     result = {
                    #         "code": 3,
                    #         "data": [],
                    #         "desc": 'Date Not Found'}
                    #     return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(BcrQeuryInventoryUpdate.QueryIUIUP(self, datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or 0,
                            'sub_activity': data[1] or 0,
                            'last_updated': data[2] or 0,
                            'volume': data[3] or 0
                        })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/iu/seam', type='json', auth="public", csrf=False)
    def getDataDashIUSeam(self, values=None):
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

                if datas:
                    # if not datas['date']:
                    #     result = {
                    #         "code": 3,
                    #         "data": [],
                    #         "desc": 'Date Not Found'}
                    #     return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                    if not datas['sub_activity']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(BcrQeuryInventoryUpdate.QueryIUSeam(self, datas['bu_id'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'inventory': data[0] or 0,
                            'iup': data[1] or 0,
                            'pit': data[2] or 0,
                            'seam': data[3] or 0,
                            'volume': data[4] or 0
                        })
                    code = 2
                    desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    # Rangking Bisnis
    @http.route('/api/dashboard/rb/table', type='json', auth="public", csrf=False)
    def getDataDashRBTable(self, values=None):
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

                if datas:
                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(BcrQeuryRangkingBU.QueryRBUTable(self, datas['date_start'], datas['date_end']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or 0,
                            'overburden': data[1] or 0,
                            'coal_getting': data[2] or 0,
                            'coal_hauling': data[3] or 0,
                            'coal_barging': data[4] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/rb/sub_activity', type='json', auth="public", csrf=False)
    def getDataDashRBSubActivity(self, values=None):
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

                if datas:
                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['sub_activity']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity End Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryRangkingBU.QueryGIUPPerSubActivity(self, datas['date_start'], datas['date_end'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or 0,
                            'sub_activity': data[1] or 0,
                            'plan': data[2] or 0,
                            'actual': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    # Rangking Kontraktor
    @http.route('/api/dashboard/rk/table', type='json', auth="public", csrf=False)
    def getDataDashRKTable(self, values=None):
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

                if datas:
                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result


                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryRangkingKontraktor.QueryRKTable(self, datas['date_start'], datas['date_end'], datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'kontraktor': data[0] or 0,
                            'overburden': data[1] or 0,
                            'coal_getting': data[2] or 0,
                            'coal_hauling': data[3] or 0,
                            'coal_barging': data[4] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/rk/kontraktor', type='json', auth="public", csrf=False)
    def getDataDashRKKontraktor(self, values=None):
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

                if datas:
                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                    if not datas['sub_activity']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryRangkingKontraktor.QueryRKGraphic(self, datas['date_start'], datas['date_end'], datas['bu_id'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'kontraktor': data[0] or 0,
                            'sub_activity': data[1] or 0,
                            'plan': data[2] or 0,
                            'actual': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    # Best Achievement
    @http.route('/api/dashboard/ba/pivot/daily', type='json', auth="public", csrf=False)
    def getDataDashBAPivotDaily(self, values=None):
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

                if datas:
                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['sub_activity']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryBestAchivement.QueryPivotTableDaily(self, datas['date_start'], datas['date_end'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'date': data[0] or 0,
                            'iup': data[1] or 0,
                            'sub_activity': data[2] or 0,
                            'volume': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/ba/pivot/monthly', type='json', auth="public", csrf=False)
    def getDataDashBAPivotMonthly(self, values=None):
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

                if datas:
                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['sub_activity']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryBestAchivement.QueryPivotTableMonthly(self, datas['date_start'], datas['date_end'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'date': data[0] or 0,
                            'iup': data[1] or 0,
                            'sub_activity': data[2] or 0,
                            'volume': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    # Production Trend

    @http.route('/api/dashboard/pt/trend/daily', type='json', auth="public", csrf=False)
    def getDataDashPTTrendDaily(self, values=None):
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

                if datas:
                    if not datas['yearmonth']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Year-Month Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                    if not datas['sub_activity']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryProductTrend.QueryPTDailySubActivity(self, datas['yearmonth'], datas['bu_id'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'date': data[0] or 0,
                            'iup': data[1] or 0,
                            'sub_activity': data[2] or 0,
                            'plan': data[3] or 0,
                            'actual': data[4] or 0,
                            'rs': data[5] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/pt/trend/monthly', type='json', auth="public", csrf=False)
    def getDataDashPTTrendMonthly(self, values=None):
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

                if datas:
                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                    if not datas['sub_activity']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sub Activity Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryProductTrend.QueryPTMonthlySubActivity(self, datas['date_start'], datas['date_end'], datas['bu_id'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'date2': data[0] or 0,
                            'date': data[1] or 0,
                            'iup': data[2] or 0,
                            'sub_activity': data[3] or 0,
                            'plan': data[4] or 0,
                            'actual': data[5] or 0,
                            'rs': data[6] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    # Jetty Activity
    @http.route('/api/dashboard/barging/jetty/activity', type='json', auth="public", csrf=False)
    def getDataDashBargingJettyActivity(self, values=None):
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

                if datas:
                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryJettyActivity.QueryJettyActivity(self, datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'mv': data[0] or 0,
                            'buyer': data[1] or 0,
                            'jetty': data[2] or 0,
                            'seq_barge': data[3] or 0,
                            'lot': data[4] or "",
                            'volume': data[5] or 0,
                            'date': data[6] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/barging/jetty/pie', type='json', auth="public", csrf=False)
    def getDataDashBargingJettyPieChart(self, values=None):
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

                if datas:
                    if not datas['date_start']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Start Not Found'}
                        return result

                    if not datas['date_end']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date End Not Found'}
                        return result

                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryJettyActivity.QueryJettyPieChart(self, datas['date_start'], datas['date_end'],
                                                             datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or 0,
                            'jetty': data[1] or 0,
                            'volume': data[2] or 0,
                            'ach': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    # Shipping Update
    @http.route('/api/dashboard/barging/su/table', type='json', auth="public", csrf=False)
    def getDataDashBargingSUTable(self, values=None):
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
                ex_data = excQueryFetchall(
                    BcrQeuryShippingUpdate.QuerySUTableUpdate(self))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'buyyer_name': data[0] or 0,
                            'market': data[1] or 0,
                            'mother_vessel': data[2] or 0,
                            'volume': data[3] or 0,
                            'last_date': data[4] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/barging/su/dmo', type='json', auth="public", csrf=False)
    def getDataDashBargingSUDMO(self, values=None):
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
                ex_data = excQueryFetchall(
                    BcrQeuryShippingUpdate.QuerySUDMOperIUP(self))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'bisnis_unit': data[0] or 0,
                            'export': data[1] or 0,
                            'domestic': data[2] or 0,
                            'dmo': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    # Realtime
    @http.route('/api/dashboard/realtime/wb/lastday', type='json', auth="public", csrf=False)
    def getDataDashRealtimeWBLastday(self, values=None):
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

                if datas:
                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryRealtimeCoalbyWeighbridge.QueryRealtimeLastDay(self, datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or 0,
                            'code': data[1] or 0,
                            'date': data[2] or 0,
                            'volume': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/realtime/wb/today', type='json', auth="public", csrf=False)
    def getDataDashRealtimeWBToday(self, values=None):
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

                if datas:
                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryRealtimeCoalbyWeighbridge.QueryRealtimeToday(self, datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or 0,
                            'code': data[1] or 0,
                            'date': data[2] or 0,
                            'volume': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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

    @http.route('/api/dashboard/realtime/wb/trendday', type='json', auth="public", csrf=False)
    def getDataDashRealtimeWBTrendday(self, values=None):
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

                if datas:
                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(
                    BcrQeuryRealtimeCoalbyWeighbridge.QueryRealtimeTrendPerDay(self,datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or 0,
                            'code': data[1] or 0,
                            'date': data[2] or 0,
                            'volume': data[3] or 0
                        })
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

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
