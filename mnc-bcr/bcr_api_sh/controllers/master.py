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


class BcrInterfaceMaster(http.Controller):

    @http.route('/api/master/iup/get', type='json', auth="public", csrf=False)
    def getDataMstIUP(self, values=None):
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
                            domain += []
                        else:
                            bu_domain = [dt.bu_company_id.id for dt in bisnis_unit_id]
                            domain += [('bu_company_id', 'in', bu_domain)]

                iup_ids = request.env['master.bisnis.unit'].sudo().search(domain)
                if iup_ids:
                    for x_data in iup_ids:
                        vals.append({
                            'bu_id': x_data.bu_company_id.id,
                            'name': x_data.name,
                            'code': x_data.code
                        })

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

    @http.route('/api/master/subactivity/get', type='json', auth="public", csrf=False)
    def getDataMstSubActivity(self, values=None):
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
                    if datas['activity']:
                        activity = request.env['master.activity'].sudo().search(
                            [('name', '=', datas['activity'])])
                        # cek data empty
                        if not activity:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'Activity Unit Not Found'}
                            return result
                        else:
                            domain += [('activity_id', '=', activity[0].id)]

                sub_activity_ids = request.env['master.sub.activity'].sudo().search(domain)
                if sub_activity_ids:
                    for x_data in sub_activity_ids:
                        if x_data.activity_id.active:
                            vals.append({
                                'id': x_data.id,
                                'name': x_data.name
                            })

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

    @http.route('/api/master/product/get', type='json', auth="public", csrf=False)
    def getDataMstProduct(self, values=None):
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
                    if datas['sub_activity_id']:
                        domain += [('sub_activity_id', '=', datas['sub_activity_id'])]

                product_ids = request.env['product.product'].sudo().search(domain)
                if product_ids:
                    for x_data in product_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name
                        })

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

    @http.route('/api/master/kontraktor/get', type='json', auth="public", csrf=False)
    def getDataMstKontraktor(self, values=None):
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

                domain += [('is_kontraktor', '=', True)]

                if datas:
                    if datas['tipe_kontraktor']:
                        domain += [('tipe_kontraktor', '=', datas['tipe_kontraktor'])]

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
                            domain += [('company_id', 'in', bu_domain)]

                kontraktor_ids = request.env['res.partner'].sudo().search(domain)
                if kontraktor_ids:
                    for x_data in kontraktor_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name
                        })

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

    @http.route('/api/master/buyer/get', type='json', auth="public", csrf=False)
    def getDataMstBuyer(self, values=None):
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

                domain += [('is_buyer', '=', True)]

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
                            domain += [('company_id', 'in', bu_domain)]

                buyer_ids = request.env['res.partner'].sudo().search(domain)
                if buyer_ids:
                    for x_data in buyer_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name
                        })

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

    @http.route('/api/master/area/get', type='json', auth="public", csrf=False)
    def getDataMstArea(self, values=None):
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

                area_ids = request.env['master.area'].sudo().search(domain)
                if area_ids:
                    for x_data in area_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name,
                            'bisnis_unit': x_data.bu_company_id.name,
                            'code': x_data.code
                        })

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

    @http.route('/api/master/source/get', type='json', auth="public", csrf=False)
    def getDataMstSource(self, values=None):
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
                        elif not datas['area_id']:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'Area Not Found'}
                            return result
                        else:
                            bu_domain = [dt.bu_company_id.id for dt in bisnis_unit_id]
                            domain += [('bu_company_id', 'in', bu_domain), ('area_code', '=', datas['area_id'])]

                source_ids = request.env['master.source'].sudo().search(domain)
                if source_ids:
                    for x_data in source_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name,
                            'bisnis_unit': x_data.bu_company_id.name,
                            'code': x_data.code
                        })

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

    @http.route('/api/master/sourcegroup/get', type='json', auth="public", csrf=False)
    def getDataMstSourceGroup(self, values=None):
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

                domain = [('name', '!=', 'BARGE')]
                vals = []

                # search domain

                sourcegroup_ids = request.env['master.sourcegroup'].sudo().search(domain)
                if sourcegroup_ids:
                    for x_data in sourcegroup_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name
                        })

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

    @http.route('/api/master/seam/get', type='json', auth="public", csrf=False)
    def getDataMstSeam(self, values=None):
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

                    if datas['area_id']:
                        domain += [('area_id', '=', datas['area_id'])]

                seam_ids = request.env['master.seam'].sudo().search(domain)
                if seam_ids:
                    for x_data in seam_ids:
                        vals.append({
                            'id': x_data.id,
                            'bisnis_unit': x_data.bu_company_id.name,
                            'area_id': x_data.area_id.id,
                            'area': x_data.area_id.name,
                            'name': x_data.code
                        })

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

    @http.route('/api/master/shift/get', type='json', auth="public", csrf=False)
    def getDataMstShift(self, values=None):
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

                    if datas['kontraktor_id']:
                        domain += [('kontraktor_id', '=', datas['kontraktor_id'])]

                shift_ids = request.env['master.shift'].sudo().search(domain)
                if shift_ids:
                    for x_data in shift_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name,
                            'code': x_data.code,
                            'bisnis_unit': x_data.bu_company_id.name,
                            'kontraktor_id': x_data.kontraktor_id.id,
                            'kontraktor': x_data.kontraktor_id.name,
                            'shiftmode_id': x_data.shiftmode_id.id,
                            'shiftmode': x_data.shiftmode_id.name,
                            'time_start': x_data.time_start,
                            'time_end': x_data.time_end,
                            'durasi': x_data.durasi
                        })

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

    @http.route('/api/master/shiftmode/get', type='json', auth="public", csrf=False)
    def getDataMstShiftMode(self, values=None):
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
                shiftmode_ids = request.env['master.shiftmode'].sudo().search(domain)
                if shiftmode_ids:
                    for x_data in shiftmode_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name
                        })

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

    @http.route('/api/master/barge/get', type='json', auth="public", csrf=False)
    def getDataMstBarge(self, values=None):
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
                barge_ids = request.env['master.barge'].sudo().search(domain)
                if barge_ids:
                    for x_data in barge_ids:
                        vals.append({
                            'id': x_data.id,
                            'code': x_data.kode_barge,
                            'name': x_data.nama_barge
                        })

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

    @http.route('/api/master/tugboat/get', type='json', auth="public", csrf=False)
    def getDataMstTugboat(self, values=None):
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
                tugboat_ids = request.env['master.tugboat'].sudo().search(domain)
                if tugboat_ids:
                    for x_data in tugboat_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name
                        })

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

    @http.route('/api/master/mv/get', type='json', auth="public", csrf=False)
    def getDataMstMV(self, values=None):
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
                mv_ids = request.env['master.mv'].sudo().search(domain)
                if mv_ids:
                    for x_data in mv_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name
                        })

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

    @http.route('/api/master/jetty/get', type='json', auth="public", csrf=False)
    def getDataMstJetty(self, values=None):
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

                jetty_ids = request.env['master.jetty'].sudo().search(domain)
                if jetty_ids:
                    for x_data in jetty_ids:
                        vals.append({
                            'id': x_data.id,
                            'bisnis_unit': x_data.bu_company_id.name,
                            'name': x_data.name,
                            'jenis': x_data.jenis
                        })

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

    @http.route('/api/master/uk/get', type='json', auth="public", csrf=False)
    def getDataMstUK(self, values=None):
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
                uk_ids = request.env['master.unit.kendaraan'].sudo().search(domain)
                if uk_ids:
                    for x_data in uk_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.nama_unit_kendaraan,
                            'code': x_data.kode_unit_kendaraan,
                            'type_id': x_data.tipe_unit_kendaraan.id,
                            'type': x_data.tipe_unit_kendaraan.name,
                            'merk_id': x_data.merek_unit_kendaraan.id,
                            'merk': x_data.merek_unit_kendaraan.name
                        })

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

    @http.route('/api/master/driver/get', type='json', auth="public", csrf=False)
    def getDataMstDriver(self, values=None):
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
                driver_ids = request.env['master.driver'].sudo().search(domain)
                if driver_ids:
                    for x_data in driver_ids:
                        vals.append({
                            'id': x_data.id,
                            'name': x_data.name,
                            'code': x_data.code,
                            'no_tlp': x_data.no_telp
                        })

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

    @http.route('/api/master/market/get', type='json', auth="public", csrf=False)
    def getDataMstMarket(self, values=None):
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
                vals =(
                        {
                            "value": "domestic",
                            "name": "Domestic Market",
                        },
                        {
                            "value": "export",
                            "name": "Export Market",
                        }
                    )
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

    @http.route('/api/master/basis/get', type='json', auth="public", csrf=False)
    def getDataMstBasis(self, values=None):
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
                vals =(
                        {
                            "value": "timbangan",
                            "name": "Timbangan",
                        },
                        {
                            "value": "ritase",
                            "name": "Ritase",
                        }
                    )
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

    @http.route('/api/master/ss/get', type='json', auth="public", csrf=False)
    def getDataMstSS(self, values=None):
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
                vals =(
                        {
                            "value": "on_progress",
                            "name": "On Progress",
                        },
                        {
                            "value": "pending",
                            "name": "Pending",
                        },
                        {
                            "value": "complete",
                            "name": "Complete",
                        }
                    )
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

    @http.route('/api/master/sizing/get', type='json', auth="public", csrf=False)
    def getDataMstSizing(self, values=None):
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
                vals = (
                        {
                            "value": "sizing",
                            "name": "Sizing",
                        },
                        {
                            "value": "not sizing",
                            "name": "Not Sizing",
                        }
                    )
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

