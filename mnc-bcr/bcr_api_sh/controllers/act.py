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

class BcrInterfaceAct(http.Controller):
    @http.route('/api/act/production/get', type='json', auth="user", csrf=False)
    def getDataProduction(self, values=None):
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
                            ('date_act', '<=', datas['date_end']),
                            ('date_act', '>=', datas['date_start'])
                        ]


                production_ids = request.env['act.production'].sudo().search(domain)
                if production_ids:
                    for x_data in production_ids:
                        obj = {
                            'id': x_data.id or 0,
                            'date': x_data.date_act or "0000-00-00",
                            'state': x_data.state or "",
                            'kode': x_data.kode or "",
                            'activity': x_data.activity_id.name or "",
                            'sub_activity_id': x_data.sub_activity_id.id or 0,
                            'sub_activity': x_data.sub_activity_id.name or "",
                            'bisnis_unit_id': x_data.bu_company_id.id or 0,
                            'bisnis_unit_name': x_data.bu_company_id.name or "",
                            'kontraktor_id': x_data.kontraktor_id.id or 0,
                            'kontraktor_name': x_data.kontraktor_id.name or "",
                            'shift_id': x_data.shift_id.id or 0,
                            'shift_name': x_data.shift_id.name or "",
                            'area_id': x_data.area_id.id or 0,
                            'area_name': x_data.area_id.name or "",
                            'source_id': x_data.source_id.id or 0,
                            'source_name': x_data.source_id.name or "",
                            'seam_code_id': x_data.seam_id.id or 0,
                            'seam_code': x_data.seam_id.code or "",
                            'product_id': x_data.product.id or 0,
                            'product': x_data.product.name or "",
                            'volume': x_data.volume or 0,
                            'ritase': x_data.ritase or 0,
                            'total_fleet': x_data.total_unit or 0,
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

    @http.route('/api/act/hauling/get', type='json', auth="user", csrf=False)
    def getDataHauling(self, values=None):
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
                                ('date_act', '<=', datas['date_end']),
                                ('date_act', '>=', datas['date_start'])
                            ]

                    hauling_ids = request.env['act.hauling'].sudo().search(domain)
                    if hauling_ids:
                        for x_data in hauling_ids:
                            obj = {
                                'id': x_data.id or 0,
                                'date': x_data.date_act or "0000-00-00",
                                'state': x_data.state or "",
                                'kode': x_data.kode or "",
                                'activity': x_data.activity_id.name or "",
                                'sub_activity_id': x_data.sub_activity_id.id or 0,
                                'sub_activity': x_data.sub_activity_id.name or "",
                                'bisnis_unit_id': x_data.bu_company_id.id or 0,
                                'bisnis_unit_name': x_data.bu_company_id.name or "",
                                'kontraktor_id': x_data.kontraktor_id.id or 0,
                                'kontraktor_name': x_data.kontraktor_id.name or "",
                                'shift_id': x_data.shift_id.id or 0,
                                'shift_name': x_data.shift_id.name or "",
                                'area_id': x_data.area_id.id or 0,
                                'area_name': x_data.area_id.name or "",
                                'product_id': x_data.product.id or 0,
                                'product': x_data.product.name or "",
                                'seam_code_id': x_data.seam_id.id or 0,
                                'seam_code': x_data.seam_id.code or "",
                                'ritase': x_data.ritase or 0,
                                'volume': x_data.volume or 0,
                                'total_unit': x_data.total_unit or 0,
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

    @http.route('/api/act/inventory/get', type='json', auth="user", csrf=False)
    def getDataInventory(self, values=None):
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
                                ('date_act', '<=', datas['date_end']),
                                ('date_act', '>=', datas['date_start'])
                            ]

                    inventory_ids = request.env['act.stockroom'].sudo().search(domain)
                    if inventory_ids:
                        for x_data in inventory_ids:
                            obj = {
                                'id': x_data.id or 0,
                                'date': x_data.date_act or "0000-00-00",
                                'state': x_data.state or "",
                                'kode': x_data.kode or "",
                                'activity': x_data.activity_id.name or "",
                                'sub_activity_id': x_data.sub_activity_id.id or 0,
                                'sub_activity': x_data.sub_activity_id.name or "",
                                'bisnis_unit_id': x_data.bu_company_id.id or 0,
                                'bisnis_unit_name': x_data.bu_company_id.name or "",
                                'area_id': x_data.area_id.id or 0,
                                'area_name': x_data.area_id.name or "",
                                'product_id': x_data.product.id or 0,
                                'product': x_data.product.name or "",
                                'seam_code_id': x_data.seam_id.id or 0,
                                'seam_code': x_data.seam_id.code or "",
                                'volume': x_data.volume or 0,
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

    @http.route('/api/act/barging/get', type='json', auth="user", csrf=False)
    def getDataBarging(self, values=None):
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
                            ('date_act', '<=', datas['date_end']),
                            ('date_act', '>=', datas['date_start'])
                        ]

                barging_ids = request.env['act.barging'].sudo().search(domain)
                if barging_ids:
                    for x_data in barging_ids:
                        obj = {
                            'id': x_data.id or 0,
                            'date': x_data.date_act or "0000-00-00",
                            'state': x_data.state or "",
                            'kode': x_data.kode or "",
                            'activity': x_data.activity_id.name or "",
                            'sub_activity_id': x_data.sub_activity_id.id or 0,
                            'sub_activity': x_data.sub_activity_id.name or "",
                            'bisnis_unit_id': x_data.bu_company_id.id or 0,
                            'bisnis_unit_name': x_data.bu_company_id.name or "",
                            'kontraktor_id': x_data.kontraktor_id.id or 0,
                            'kontraktor_name': x_data.kontraktor_id.name or "",
                            'kontraktor_prod_id': x_data.kontraktor_produksi_id.id or 0,
                            'kontraktor_prod_name': x_data.kontraktor_produksi_id.name or "",
                            'shift_id': x_data.shift_id.id or 0,
                            'shift_name': x_data.shift_id.name or "",
                            'seq_barge': x_data.seq_barge or 0,
                            'lot': x_data.lot or "",
                            'area_id': x_data.area_id.id or 0,
                            'area_name': x_data.area_id.name or "",
                            'seam_code_id': x_data.seam_id.id or 0,
                            'seam_code': x_data.seam_id.code or "",
                            'product_id': x_data.product.id or 0,
                            'product': x_data.product.name or "",
                            'ritase': x_data.ritase or 0,
                            'volume': x_data.volume or 0,
                            'total_fleet': x_data.total_unit or 0,
                            'source_group_id': x_data.source_group.id or 0,
                            'source_group_name': x_data.source_group.name or "",
                            'basis': x_data.basis or "",
                            'sizing': x_data.sizing or "",
                            'barge_id': x_data.barge_id.id or 0,
                            'barge_name': x_data.barge_id.nama_barge or "",
                            'tugboat_id': x_data.tugboat_id.id or 0,
                            'tugboat_name': x_data.tugboat_id.name or "",
                            'mv_id': x_data.mv_boat_id.id or 0,
                            'mv_name': x_data.mv_boat_id.name or "",
                            'jetty_id': x_data.jetty_id.id or 0,
                            'jetty_name': x_data.jetty_id.name or "",
                            'buyer_id': x_data.buyer_id.id or 0,
                            'buyer_name': x_data.buyer_id.name or "",
                            'market': x_data.market or "",
                            'status_shipper': x_data.status_shipper or "",
                            'remarks': x_data.remarks or "",
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

    @http.route('/api/act/delay/get', type='json', auth="user", csrf=False)
    def getDataDelay(self, values=None):
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
                                ('date_act', '<=', datas['date_end']),
                                ('date_act', '>=', datas['date_start'])
                            ]

                    delay_ids = request.env['act.delay'].sudo().search(domain)
                    if delay_ids:
                        for x_data in delay_ids:
                            obj = {
                                'id': x_data.id or 0,
                                'date': x_data.date_act or "0000-00-00",
                                'state': x_data.state or "",
                                'kode': x_data.kode or 0,
                                'activity': x_data.activity_id.name or "",
                                'sub_activity_id': x_data.sub_activity_id.id or 0,
                                'sub_activity': x_data.sub_activity_id.name or "",
                                'bisnis_unit_id': x_data.bu_company_id.id or 0,
                                'bisnis_unit_name': x_data.bu_company_id.name or "",
                                'kontraktor_id': x_data.kontraktor_id.id or 0,
                                'kontraktor_name': x_data.kontraktor_id.name or "",
                                'shift_id': x_data.shift_id.id or 0,
                                'shift_name': x_data.shift_id.name or "",
                                'area_id': x_data.area_id.id or 0,
                                'area_name': x_data.area_id.name or "",
                                'product_id': x_data.product.id or 0,
                                'product': x_data.product.name or "",
                                'volume': x_data.volume or 0,
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
