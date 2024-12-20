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


class BcrInterfaceActReview(http.Controller):
    @http.route('/api/act/hauling/review', type='json', auth="public", csrf=False)
    def getDataActHaulingReview(self, values=None):
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

                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['kontraktor_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Kontraktor Id Not Found'}
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

                    if not datas['area_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Area Id Not Found'}
                        return result

                    if not datas['shift_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Shift Id Not Found'}
                        return result

                    if datas['seam_id'] == "":
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Seam Id Not Found'}
                        return result

                    if not datas['ritase']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Ritase Not Found'}
                        return result

                    if not datas['volume']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Volume Not Found'}
                        return result

                    if not datas['total_unit']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Total Unit Not Found'}
                        return result

                    if not datas['tipe_review']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tipe Review Not Found'}
                        return result

                    desc = ""
                    code = 0
                    hauling_data = request.env['act.hauling'].sudo().search(domain)
                    if hauling_data:
                        if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, hauling_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "review")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result
                        # 2 untuk merubah state review
                        if datas['tipe_review'] == 2:
                            hauling_data.write(
                                {
                                    "state": "approve",
                                    "date_act": datas['date'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "shift_id": datas['shift_id'],
                                    "seam_id": datas['seam_id'],
                                    "ritase": datas['ritase'],
                                    "volume": datas['volume'],
                                    "total_unit": datas['total_unit']
                                }
                            )
                        else:
                            hauling_data.write(
                                {
                                    "date_act": datas['date'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "shift_id": datas['shift_id'],
                                    "seam_id": datas['seam_id'],
                                    "ritase": datas['ritase'],
                                    "volume": datas['volume'],
                                    "total_unit": datas['total_unit']
                                }
                            )
                        vals.append({
                            'id': hauling_data.id,
                            'kode': hauling_data.kode
                        })
                        code = 2
                        desc = "Success"

                        src_usr_val = BcrInterfaceNotification.search_usr_validation_by_model(self,"validation_act_hauling_id",datas['id'], "approve")
                        if src_usr_val:
                            for user in src_usr_val:
                                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"act.hauling","approve",hauling_data.kode)

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

    @http.route('/api/act/barging/review', type='json', auth="public", csrf=False)
    def getDataActBargingReview(self, values=None):
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

                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['kontraktor_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Kontraktor Id Not Found'}
                        return result

                    if not datas['kontraktor_produksi_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Kontraktor Produksi Id Not Found'}
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

                    if not datas['area_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Area Id Not Found'}
                        return result

                    if not datas['shift_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Shift Id Not Found'}
                        return result

                    if datas['seam_id'] == "":
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Seam Id Not Found'}
                        return result

                    if not datas['source_group_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Source Group Id Not Found'}
                        return result

                    if not datas['ritase']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Ritase Not Found'}
                        return result

                    if not datas['volume']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Volume Not Found'}
                        return result

                    if not datas['total_fleet']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Total Fleet Not Found'}
                        return result

                    if not datas['barge_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Barge Id Not Found'}
                        return result

                    if datas['seam_id'] == "":
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Seam Id Not Found'}
                        return result

                    if not datas['tugboat_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tugboat Id Not Found'}
                        return result

                    if not datas['market']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Market Not Found'}
                        return result

                    if not datas['mv_boat_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'MV Boat Id Not Found'}
                        return result

                    if not datas['jetty_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Jetty Id Not Found'}
                        return result

                    if not datas['buyer_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Buyer Id Not Found'}
                        return result

                    if not datas['basis']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Basis Not Found'}
                        return result

                    if not datas['status_shipper']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Status Shipper Not Found'}
                        return result

                    if not datas['remarks']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Remarks Shipper Not Found'}
                        return result

                    if not datas['sizing']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Sizing Not Found'}
                        return result

                    if not datas['seq_barge']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Seq Barge Not Found'}
                        return result

                    if not datas['tipe_review']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tipe Review Not Found'}
                        return result

                    if not datas['lot']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tipe Review Not Found'}
                        return result

                    desc = ""
                    code = 0
                    barging_data = request.env['act.barging'].sudo().search(domain)
                    if barging_data:
                        # if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, datas['date']):
                        if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, barging_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "review")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result
                        # 2 untuk merubah state review
                        if datas['tipe_review'] == 2:
                            barging_data.write(
                                {
                                    "state": "approve",
                                    "date_act": datas['date'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "kontraktor_produksi_id": datas['kontraktor_produksi_id'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "shift_id": datas['shift_id'],
                                    "seam_id": datas['seam_id'],
                                    "ritase": datas['ritase'],
                                    "volume": datas['volume'],
                                    "total_unit": datas['total_fleet'],
                                    "source_group": datas['source_group_id'],
                                    "barge_id": datas['barge_id'],
                                    "tugboat_id": datas['tugboat_id'],
                                    "market": datas['market'],
                                    "mv_boat_id": datas['mv_boat_id'],
                                    "jetty_id": datas['jetty_id'],
                                    "buyer_id": datas['buyer_id'],
                                    "lot": datas['lot'],
                                    "basis": datas['basis'],
                                    "status_shipper": datas['status_shipper'],
                                    "sizing": datas['sizing'],
                                    "seq_barge": datas['seq_barge'],
                                    "remarks": datas['remarks']
                                }
                            )
                        else:
                            barging_data.write(
                                {
                                    "date_act": datas['date'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "kontraktor_produksi_id": datas['kontraktor_produksi_id'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "shift_id": datas['shift_id'],
                                    "seam_id": datas['seam_id'],
                                    "ritase": datas['ritase'],
                                    "volume": datas['volume'],
                                    "total_unit": datas['total_fleet'],
                                    "source_group": datas['source_group_id'],
                                    "barge_id": datas['barge_id'],
                                    "tugboat_id": datas['tugboat_id'],
                                    "market": datas['market'],
                                    "mv_boat_id": datas['mv_boat_id'],
                                    "jetty_id": datas['jetty_id'],
                                    "buyer_id": datas['buyer_id'],
                                    "basis": datas['basis'],
                                    "lot": datas['lot'],
                                    "status_shipper": datas['status_shipper'],
                                    "sizing": datas['sizing'],
                                    "seq_barge": datas['seq_barge'],
                                    "remarks": datas['remarks']
                                }
                            )
                        vals.append({
                            'id': barging_data.id,
                            'kode': barging_data.kode
                        })
                        code = 2
                        desc = "Success"

                        src_usr_val = BcrInterfaceNotification.search_usr_validation_by_model(self,"validation_act_barging_id",datas['id'], "approve")
                        if src_usr_val:
                            for user in src_usr_val:
                                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"act.barging","approve",barging_data.kode)

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

    @http.route('/api/act/production/review', type='json', auth="public", csrf=False)
    def getDataActProductionReview(self, values=None):
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

                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['kontraktor_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Kontraktor Id Not Found'}
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

                    if not datas['area_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Area Id Not Found'}
                        return result

                    if not datas['shift_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Shift Id Not Found'}
                        return result

                    if datas['seam_id'] == "":
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Seam Id Not Found'}
                        return result

                    if not datas['source_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Source Id Not Found'}
                        return result

                    if not datas['ritase']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Ritase Not Found'}
                        return result

                    if not datas['volume']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Volume Not Found'}
                        return result

                    if not datas['total_fleet']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Total Fleet Not Found'}
                        return result

                    if not datas['tipe_review']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tipe Review Not Found'}
                        return result

                    desc = ""
                    code = 0
                    production_data = request.env['act.production'].sudo().search(domain)
                    if production_data:
                        # if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, datas['date']):
                        if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, production_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "review")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result

                        if datas['seam_id'] == 0 or datas['seam_id'] == "0":
                            datas['seam_id'] = False
                        # 2 untuk merubah state review
                        if datas['tipe_review'] == 2:
                            production_data.write(
                                {
                                    "state": "approve",
                                    "date_act": datas['date'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "shift_id": datas['shift_id'],
                                    "seam_id": datas['seam_id'],
                                    "ritase": datas['ritase'],
                                    "volume": datas['volume'],
                                    "total_unit": datas['total_fleet'],
                                    "source_id": datas['source_id']
                                }
                            )
                        else:
                            production_data.write(
                                {
                                    "date_act": datas['date'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "shift_id": datas['shift_id'],
                                    "seam_id": datas['seam_id'],
                                    "ritase": datas['ritase'],
                                    "volume": datas['volume'],
                                    "total_unit": datas['total_fleet'],
                                    "source_id": datas['source_id']
                                }
                            )
                        vals.append({
                            'id': production_data.id,
                            'kode': production_data.kode
                        })
                        code = 2
                        desc = "Success"

                        src_usr_val = BcrInterfaceNotification.search_usr_validation_by_model(self,"validation_act_production_id",datas['id'], "approve")
                        if src_usr_val:
                            for user in src_usr_val:
                                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"act.production", "approve",production_data.kode)

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

    @http.route('/api/act/inventory/review', type='json', auth="public", csrf=False)
    def getDataActInventoryReview(self, values=None):
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

                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
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

                    if not datas['area_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Area Id Not Found'}
                        return result

                    if datas['seam_id'] == "":
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Seam Id Not Found'}
                        return result

                    # if not datas['volume']:
                    #     result = {
                    #         "code": 3,
                    #         "data": [],
                    #         "desc": 'Volume Not Found'}
                    #     return result
                    if not datas['tipe_review']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Tipe Review Not Found'}
                        return result

                    desc = ""
                    code = 0
                    stockroom_data = request.env['act.stockroom'].sudo().search(domain)
                    if stockroom_data:
                        # if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, datas['date']):
                        if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, stockroom_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "review")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result

                        # 2 untuk merubah state review
                        if datas['tipe_review'] == 2:
                            stockroom_data.write(
                                {
                                    "state": "approve",
                                    "date_act": datas['date'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "seam_id": datas['seam_id'],
                                    "volume": datas['volume']
                                }
                            )
                        else:
                            stockroom_data.write(
                                {
                                    "date_act": datas['date'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "seam_id": datas['seam_id'],
                                    "volume": datas['volume']
                                }
                            )
                        vals.append({
                            'id': stockroom_data.id,
                            'kode': stockroom_data.kode
                        })
                        code = 2
                        desc = "Success"

                        src_usr_val = BcrInterfaceNotification.search_usr_validation_by_model(self,"validation_act_stockroom_id",datas['id'], "approve")
                        if src_usr_val:
                            for user in src_usr_val:
                                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"act.stockroom","approve",stockroom_data.kode)

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

    @http.route('/api/act/delay/review', type='json', auth="public", csrf=False)
    def getDataActDelayReview(self, values=None):
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

                    if not datas['date']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Date Not Found'}
                        return result

                    if not datas['kontraktor_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Kontraktor Id Not Found'}
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

                    if not datas['area_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Area Id Not Found'}
                        return result

                    if not datas['shift_id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Shift Id Not Found'}
                        return result

                    if not datas['volume']:
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
                    delay_data = request.env['act.delay'].sudo().search(domain)
                    if delay_data:
                        # if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, datas['date']):
                        if BcrDateLock.cek_date_lock_act(self, "review", request.env.user.id, delay_data.write_date.date()):
                            cek_date_lock_act_message = BcrDateLock.cek_date_lock_act_message(self, "review")
                            result = {
                                "code": 5,
                                "message_date_lock": cek_date_lock_act_message,
                                "desc": 'Failed Date Lock'}
                            return result

                        # 2 untuk merubah state review
                        if datas['tipe_review'] == 2:
                            delay_data.write(
                                {
                                    "state": "approve",
                                    "date_act": datas['date'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "shift_id": datas['shift_id'],
                                    "volume": datas['volume']
                                }
                            )
                        else:
                            delay_data.write(
                                {
                                    "date_act": datas['date'],
                                    "kontraktor_id": datas['kontraktor_id'],
                                    "sub_activity_id": datas['sub_activity_id'],
                                    "product": datas['product_id'],
                                    "area_id": datas['area_id'],
                                    "shift_id": datas['shift_id'],
                                    "volume": datas['volume']
                                }
                            )
                        vals.append({
                            'id': delay_data.id,
                            'kode': delay_data.kode
                        })
                        code = 2
                        desc = "Success"

                        src_usr_val = BcrInterfaceNotification.search_usr_validation_by_model(self,"validation_act_delay_id",datas['id'], "approve")
                        if src_usr_val:
                            for user in src_usr_val:
                                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"act.delay","approve",delay_data.kode)

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
