import logging
import pytz
import json
from datetime import datetime, date
from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.tools.safe_eval import safe_eval

from pytz import utc
from odoo import api, fields, models, tools
from calendar import month_name
# from .query_dashboard import BcrQeuryResume,BcrQeuryInventoryUpdate,BcrQeuryRangkingKontraktor,\
#     BcrQeuryRangkingBU,BcrQeuryBestAchivement,BcrQeuryJettyActivity,BcrQeuryShippingUpdate,\
#     BcrQeuryProductTrend,BcrQeuryRealtimeCoalbyWeighbridge

from odoo.addons.bcr_api_sh.controllers.dashboard import BcrInterfaceDashboard
from odoo.addons.bcr_api_sh.controllers.main import BcrInterface
# from odoo.addons.bcr_api_sh.controllers.query_dashboard import BcrQeuryResume
from .query_miners import QeuryResumeMiners, QeuryRankingBUMiners, QueryRankingKontraktorMiners, BcrQeuryBestAchivementMiners, QeuryProductTrendMiners, QeuryJettyActivityMiners, QeuryOutlookMiners, QeuryShippingUpdate, QueryJoinSurvey, QeuryInventoryUpdateMiners

# try:
#     import simplejson as json
# except ImportError:
#     import json

_logger = logging.getLogger(__name__)

DATETIMEFORMAT = '%Y-%m-%d %H:%M:%S'
DATEFORMAT = '%Y-%m-%d'
LOCALTZ = pytz.timezone('Asia/Jakarta')


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


def excQueryFetchall(query):
    request.env.cr.execute(query)
    fetch_data = request.env.cr.fetchall()
    return fetch_data


def create_complete_nested_dict(data):
    result = {}
    all_mon_years = sorted(set(entry['mon_year'] for entry in data), key=lambda x: datetime.strptime(x, '%b %Y'))

    for entry in data:
        pit = entry['pit']
        iup = 'Month Year'
        mon_year = entry['mon_year']
        volume = entry['volume']

        if pit not in result:
            result[pit] = {}

        if iup not in result[pit]:
            result[pit][iup] = {my: 0.0 for my in all_mon_years}

        result[pit][iup][mon_year] = volume

    # Ensure all mon_year keys are present for each pit/iup
    for pit in result:
        for iup in result[pit]:
            for mon_year in all_mon_years:
                if mon_year not in result[pit][iup]:
                    result[pit][iup][mon_year] = 0.0

    return result


def get_coal_company(self):
    coal_company = request.env['ir.config_parameter'].sudo().get_param('coal_company') or []
    return coal_company


class BcrInterface(BcrInterface):

    @http.route('/api/account/detail/get', type='json', auth="user")
    def getDataAccount(self, values=None):
        res = super(BcrInterface, self).getDataAccount(values)
        if res['code'] == 2:
            coal_company = get_coal_company(self)
            user = request.env.user
            access_dashboard = False

            company_coal = []
            for comp in user.company_ids:
                if str(comp.id) in coal_company:
                    code_comp = request.env['master.bisnis.unit'].sudo().search(
                        [('bu_company_id', '=', comp.id)], limit=1).code
                    if code_comp:
                        company_coal.append({
                            'id': comp.id,
                            'code': code_comp,
                            'name': comp.name
                        })
            if len(company_coal) > 0:
                access_dashboard = True

            res['data']['user_companies']['company_coal'] = company_coal
            res['data']['access_dashboard'] = access_dashboard

        return res


class BcrInterfaceDashboard(BcrInterfaceDashboard):

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
                # domain = []
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
                ex_data = excQueryFetchall(QeuryResumeMiners.QueryTableOverview(self, datas['date'], datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        print("DATA")
                        vals.append({
                            'item': data[0] or 0,
                            'coal_getting': data[1] or 0,
                            'overburden': data[2] or 0,
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
        return False

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
                # domain = []
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
                ex_data = excQueryFetchall(QeuryResumeMiners.QueryCGMTD(self, datas['date'], datas['bu_id']))
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
                # domain = []
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

                ex_data = excQueryFetchall(QeuryResumeMiners.QueryCGYTD(self, datas['date'], datas['bu_id']))
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
                    result = {
                        "code": 4,
                        "desc": 'Data is Empty'
                    }
                    return result

                datas = values
                # domain = []
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

                ex_data = excQueryFetchall(QeuryResumeMiners.QueryOBMTD(self, datas['date'], datas['bu_id']))
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
                # domain = []
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

                ex_data = excQueryFetchall(QeuryResumeMiners.QueryOBYTD(self, datas['date'], datas['bu_id']))
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
                # domain = []
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

                ex_data = excQueryFetchall(QeuryResumeMiners.QueryHaulingMTD(self, datas['date'], datas['bu_id']))
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
                # domain = []
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

                ex_data = excQueryFetchall(QeuryResumeMiners.QueryHaulingYTD(self, datas['date'], datas['bu_id']))
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

                ex_data = excQueryFetchall(QeuryResumeMiners.QueryBargingMTD(self, datas['date'], datas['bu_id']))
                for data in ex_data:
                    if data[0] == "PLAN MTD":
                        plan_mtd = data[1]
                    if data[0] == "AKTUAL MTD":
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

                ex_data = excQueryFetchall(QeuryResumeMiners.QueryBargingYTD(self, datas['date'], datas['bu_id']))
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
                # domain = []
                vals = []

                if datas:
                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(QeuryInventoryUpdateMiners.QueryIUSubActivity(self, datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'sub_activity': data[0] or '',
                            'volume': data[1] or 0.0,
                            'last_updated': data[2] or ''
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
                # domain = []
                vals = []

                if datas:
                    if not datas['bu_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Bisnis Unit Not Found'}
                        return result

                # search domain
                ex_data = excQueryFetchall(QeuryInventoryUpdateMiners.QueryIUIUP(self, datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'sub_activity': data[0] or '',
                            'iup': data[1] or '',
                            'volume': data[2] or 0.0,
                            'last_updated': data[3] or ''
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
                # domain = []
                vals = []

                if datas:
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
                ex_data = excQueryFetchall(QeuryInventoryUpdateMiners.QueryIUSeam(self, datas['bu_id'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'inventory': data[0] or '',
                            'iup': data[1] or '',
                            'source': data[2] or 0.0,
                            'volume': data[3] or 0.0,
                            'last_updated': data[4] or ''
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

    # Ranking Bisnis Unit
    @http.route('/api/dashboard/rb/table', type='json', auth="public", csrf=False)
    def getDataDashRBTable(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                datas = values
                # domain = []
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
                ex_data = excQueryFetchall(QeuryRankingBUMiners.QueryRBUTable(self, datas['date_start'], datas['date_end']))
                if ex_data:
                    for data in ex_data:
                        if data != 0:
                            vals.append({
                                'iup': data[0] or "",
                                'coal_getting': data[1] or 0,
                                'overburden': data[2] or 0,
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
                # domain = []
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
                ex_data = excQueryFetchall(QeuryRankingBUMiners.QueryGIUPPerSubActivity(self, datas['date_start'], datas['date_end'], datas['sub_activity']))
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
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                datas = values
                # domain = []
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
                    QueryRankingKontraktorMiners.QueryRKTable(self, datas['date_start'], datas['date_end'], datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        print("=====data=====")
                        print(data)
                        if data[0]:
                            vals.append({
                                'kontraktor': data[0] or "",
                                'coal_getting': data[1] or 0,
                                'overburden': data[2] or 0,
                                'coal_hauling': data[3] or 0
                                # 'coal_barging': data[4] or 0
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
                # domain = []
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
                ex_data = excQueryFetchall(QueryRankingKontraktorMiners.QueryRKGraphic(self, datas['date_start'], datas['date_end'], datas['bu_id'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        if data[0]:
                            vals.append({
                                'kontraktor': data[0] or "",
                                'sub_activity': data[1] or "",
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
                # domain = []
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
                    BcrQeuryBestAchivementMiners.QueryPivotTableDaily(self, datas['date_start'], datas['date_end'], datas['sub_activity']))
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
                # domain = []
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
                    BcrQeuryBestAchivementMiners.QueryPivotTableMonthly(self, datas['date_start'], datas['date_end'], datas['sub_activity']))
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

    # Product Trend
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
                # domain = []
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
                    QeuryProductTrendMiners.QueryPTMonthlySubActivity(self, datas['date_start'], datas['date_end'], datas['bu_id'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        code_comp = request.env['master.bisnis.unit'].sudo().search(
                            [('bu_company_id.name', '=', data[2])], limit=1).code or ""
                        vals.append({
                            'date2': data[0] or "",
                            'date': data[1] or "",
                            'iup': code_comp,
                            'sub_activity': data[3] or "",
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
                # domain = []
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
                    QeuryProductTrendMiners.QueryPTDailySubActivity(self, datas['yearmonth'], datas['bu_id'], datas['sub_activity']))
                if ex_data:
                    for data in ex_data:
                        code_comp = request.env['master.bisnis.unit'].sudo().search(
                            [('bu_company_id.name', '=', data[1])], limit=1).code or ""
                        vals.append({
                            'date': data[0] or "",
                            'iup': code_comp,
                            'sub_activity': data[2] or "",
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
                # domain = []
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
                    QeuryJettyActivityMiners.QueryJettyActivity(self, datas['bu_id']))

                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'jetty_name': data[0] or "",
                            'buyer': data[1] or "",
                            'carrier': data[2] or "",
                            'volume_act': data[3] or 0,
                            'ach': data[4] or 0,
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
                # domain = []
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
                res_vals = []
                ex_data = excQueryFetchall(
                    QeuryJettyActivityMiners.QueryJettyPieChart(self, datas['date_start'], datas['date_end'], datas['bu_id']))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or 0,
                            'jetty': data[1] or 0,
                            'volume': data[2] or 0,
                            'ach': data[3] or 0
                        })
                        jetty_data = {}

                        for entry in vals:
                            jetty = entry["jetty"]
                            if jetty not in jetty_data:
                                jetty_data[jetty] = {"volume": 0, "ach": 0}
                            jetty_data[jetty]["volume"] += entry["volume"]
                            jetty_data[jetty]["ach"] += entry["ach"]

                        # To calculate the average ACH for each jetty
                        for jetty, values in jetty_data.items():
                            count = len([e for e in vals if e["jetty"] == jetty])
                            values["ach"] /= count

                        res_vals = [{"jetty": jetty, "volume": values["volume"], "ach": values["ach"]} for jetty, values in jetty_data.items()]
                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

                result = {
                    "code": code,
                    "data": res_vals,
                    "desc": desc
                }
                return result
            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    # Outlook
    @http.route('/api/dashboard/outlook/table/pit', type='json', auth="public", csrf=False)
    def getDataDashOutlookTablePit(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                # datas = values
                # domain = []
                vals = []
                res_vals =[]
                ex_data = excQueryFetchall(
                    QeuryOutlookMiners.QueryOutlookPit(self))
                # Filtering Data
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'date': data[0] or "",
                            'iup': data[1] or "",
                            'pit': data[2] or "",
                            'volume': data[3] or 0,
                            'mon_year': data[4] or "",
                            'yyyymm': data[5] or ""
                        })

                    datas = create_complete_nested_dict(vals)
                    for x_data in datas:
                        monthly_datas = list(datas[x_data]['Month Year'].values())
                        monthly_datas += [0.0] * (3 - len(monthly_datas))
                        # if len(monthly_datas) != 3:
                        #     datas_1 = monthly_datas[0]
                        #     datas_2 = monthly_datas[1] if monthly_datas[1] else 0.0
                        #     datas_3 = monthly_datas[2] if monthly_datas[2] else 0.0
                        # else:
                        #     datas_1 = monthly_datas[0]
                        #     datas_2 = monthly_datas[1]
                        #     datas_3 = monthly_datas[2]
                        res_data = {}
                        res_data['pit'] = x_data
                        res_data['month1'] = monthly_datas[0]
                        res_data['month2'] = monthly_datas[1]
                        res_data['month3'] = monthly_datas[2]
                        res_vals.append(res_data)

                        code = 2
                        desc = "Success"
                else:
                    code = 1
                    desc = "Data Not Found"

                result = {
                    "code": code,
                    "data": res_vals,
                    "desc": desc
                }
                return result

            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/dashboard/outlook/monhtly/iup', type='json', auth="public", csrf=False)
    def getDataDashOutlookMonthlyIup(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                # datas = values
                # domain = []
                vals = []
                ex_data = excQueryFetchall(
                    QeuryOutlookMiners.QueryOutlookMonthlyIup(self))
                # Filtering Data
                if ex_data:
                    print(ex_data)
                    # datas = create_complete_nested_dict(ex_data)
                    # print("SSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
                    # print(datas)
                    for data in ex_data:
                        code_comp = request.env['master.bisnis.unit'].sudo().search(
                            [('bu_company_id.name', '=', data[0])], limit=1).code or ""
                        vals.append({
                            'iup': code_comp,
                            'category': data[1] or "",
                            'plan_3mrp': data[2] or 0,
                            'outlook': data[3] or 0,
                            'ach': data[4] or 0,
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

    @http.route('/api/dashboard/outlook/yearly/iup', type='json', auth="public", csrf=False)
    def getDataDashOutlookYearlyIup(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                # datas = values
                # domain = []
                vals = []
                ex_data = excQueryFetchall(
                    QeuryOutlookMiners.QueryOutlookYearlyIup(self))
                # Filtering Data
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'mon_year': data[0] or "",
                            'yyyymm': data[1] or "",
                            'plan': data[2] or 0,
                            'outlook': data[3] or 0
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

    @http.route('/api/dashboard/outlook/detail/iup', type='json', auth="public", csrf=False)
    def getDataDashOutlookDetailIup(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                else:
                    result = {"code": 4,
                              "desc": 'Data is Empty'}
                    return result

                # datas = values
                # domain = []
                vals = []
                ex_data = excQueryFetchall(
                    QeuryOutlookMiners.QueryOutlookIup(self))
                # Filtering Data
                if ex_data:
                    for data in ex_data:
                        code_comp = request.env['master.bisnis.unit'].sudo().search(
                            [('bu_company_id.name', '=', data[0])], limit=1).code or ""
                        vals.append({
                            'iup': code_comp or "",
                            'outlook': data[1] or 0
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

                # datas = values
                # domain = []
                vals = []

                # search domain
                ex_data = excQueryFetchall(
                    QeuryShippingUpdate.QuerySUTableUpdate(self))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'buyyer_name': data[0] or "",
                            'plan': data[1] or 0,
                            'progress': data[2] or 0,
                            'status': data[3] or "",
                            'shipping_id': data[4] or 0,
                            'market': data[5] or "",
                            'last_barge': data[6] or "",
                            'actual': data[7] or 0
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

                # datas = values
                # domain = []
                vals = []

                # search domain
                ex_data = excQueryFetchall(
                    QeuryShippingUpdate.QuerySUDMOperIUP(self))
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'bisnis_unit': data[0] or 0,
                            'domestic': data[1] or 0,
                            'export': data[2] or 0,
                            'plan_rkab': data[3] or 0,
                            'dmo': data[4] or 0
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

    # Survey
    @http.route('/api/dashboard/survey/ob/weekly', type='json', auth="public", csrf=False)
    def getDataDashSurveyOB(self, values=None):
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
                # search domain
                ex_data = excQueryFetchall(
                    QueryJoinSurvey.QuerySurveyOB(self, datas['yearmonth'], datas['bu_id']))
                print("==============")
                print(ex_data)
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or "",
                            'yyyymm': data[1] or "",
                            'tc': data[2] or 0,
                            'survey': data[3] or 0,
                            'prosentase': data[4] or 0
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

    @http.route('/api/dashboard/survey/cg/weekly', type='json', auth="public", csrf=False)
    def getDataDashSurveyCG(self, values=None):
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
                # search domain
                ex_data = excQueryFetchall(
                    QueryJoinSurvey.QuerySurveyCG(self, datas['yearmonth'], datas['bu_id']))
                print("==============")
                print(ex_data)
                if ex_data:
                    for data in ex_data:
                        vals.append({
                            'iup': data[0] or "",
                            'yyyymm': data[1] or "",
                            'tc': data[2] or 0,
                            'survey': data[3] or 0,
                            'prosentase': data[4] or 0
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
