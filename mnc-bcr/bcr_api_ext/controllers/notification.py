import logging
import json
from datetime import datetime, date, timedelta
from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo import api, fields, models, tools

from odoo.addons.bcr_api_sh.controllers.main import BcrInterface


_logger = logging.getLogger(__name__)


def paginate_data(data, page_number, items_per_page):
    total_items = len(data)
    total_pages = (total_items + items_per_page - 1) // items_per_page

    if page_number < 1 or page_number > total_pages:
        return {"error": "Invalid page number"}

    start_index = (page_number - 1) * items_per_page
    end_index = min(start_index + items_per_page, total_items)

    paginated_data = data[start_index:end_index]
    return {
        "total_pages": total_pages,
        "current_page": page_number,
        "data": paginated_data
    }


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


class BcrInterface(BcrInterface):

    @http.route('/api/account/notif/count', type='json', auth="user", methods=['GET'])
    def CountNotification(self, values=None):
        user = request.env.user
        if user:
            if request.httprequest.headers.get('Api-key'):
                key = request.httprequest.headers.get('Api-key')
                api_key = get_api_key(self)
                if key == api_key:
                    # if request.httprequest.data:
                    #     parameter = json.loads(request.httprequest.data)
                    obj = request.env['push.notification'].sudo()
                    data_log = obj.search(
                        [('user', '=', user.id), ('is_read', '=', False)], order='create_date desc')
                    total = len(data_log.ids) or 0
                    # Return Datas
                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": [
                            {
                                "total": total
                            }
                        ]
                    }
                    return result

                else:
                    result = {
                        "code": 3,
                        "desc": 'Failed to authentication'}
                    return result
            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/account/notif/delete', type='json', auth="user")
    def DeletNotification(self, values=None):
        user = request.env.user
        if user:
            if request.httprequest.headers.get('Api-key'):
                key = request.httprequest.headers.get('Api-key')
                api_key = get_api_key(self)
                if key == api_key:
                    if request.httprequest.data:
                        parameter = json.loads(request.httprequest.data)
                    if len(parameter['ids']) <= 0:
                        result = {
                            "code": 3,
                            "desc": "Please add id notification"
                        }
                        return result
                    for res_id in parameter['ids']:
                        notif_id = request.env['push.notification'].browse(res_id)
                        if notif_id:
                            notif_id.unlink()
                        else:
                            result = {
                                "code": 3,
                                "desc": 'Data Not Found'
                            }
                            return result
                    result = {
                        "code": 2,
                        "desc": "Success",
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "desc": 'Failed to authentication'}
                    return result
            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/account/notif/as_read', type='json', auth="user")
    def MarkAsReadNotification(self, values=None):
        user = request.env.user
        if user:
            if request.httprequest.headers.get('Api-key'):
                key = request.httprequest.headers.get('Api-key')
                api_key = get_api_key(self)
                if key == api_key:
                    if request.httprequest.data:
                        parameter = json.loads(request.httprequest.data)
                    res_data = []
                    if len(parameter['ids']) <= 0:
                        result = {
                            "code": 3,
                            "desc": "Please add id notification"
                        }
                        return result
                    for res_id in parameter['ids']:
                        notif_id = request.env['push.notification'].browse(res_id)
                        if notif_id:
                            notif_id.write({
                                'is_read': True
                            })
                            res_data.append(res_id)
                        else:
                            result = {
                                "code": 3,
                                "desc": 'Data Not Found'
                            }
                            return result
                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "desc": 'Failed to authentication'}
                    return result
            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/account/get/logger-notification', type='json', auth="user")
    def getDataLoggerNotification(self, values=None):
        user = request.env.user
        if user:
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
                    res_data = []
                    obj = request.env['push.notification'].sudo()
                    if len(datas['iup']) > 0:
                        data_log = obj.search(
                            [('user', '=', user.id), ('company', 'in', datas['iup'])])
                    else:
                        data_log = obj.search(
                            [('user', '=', user.id)], order='create_date desc')

                    if data_log:
                        for x_data in data_log.filtered(lambda x: not x.is_read):
                            obj = {
                                'id': x_data.id or 0,
                                'create_date': (x_data.create_date + timedelta(hours=7)) or "0000-00-00",
                                'company': x_data.company.name or "All",
                                'user': x_data.user.name or 0,
                                'title': x_data.title or "",
                                'code': x_data.code or "OV",
                                'action': x_data.action or "OV",
                                'message': x_data.message or "",
                                'is_read': x_data.is_read,
                                'data_id': x_data.res_id or 0,
                            }
                            res_data.append(obj)
                        # ===================================================================================
                        # Jumlah total halaman
                        page_number = int(request.httprequest.args.get('page')) 
                        if res_data:
                            res_data = sorted(res_data, key=lambda x: x['create_date'], reverse=True)
                            # ==============================================
                            items_per_page = 10  # Example items per page

                            total_pages = (len(res_data) + items_per_page - 1) // items_per_page
                            if page_number > total_pages or page_number <= 0:
                                result = {
                                    "code": 3,
                                    "desc": "pages must be below the total page",
                                    "data": [],
                                }
                                return result
                            # Call the paginate_data function
                            paginated_result = paginate_data(res_data, page_number, items_per_page)
                        else:
                            total_pages = 1
                            paginated_result = {'data': []}
                        # ===================================================================================
                        result = {
                            "code": 2,
                            "desc": "Success",
                            "total_pages": total_pages,
                            "page": page_number,
                            "data": paginated_result['data']
                        }
                        return result
                        # ===================================================================================
                    else:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": "Data Not Found"
                        }
                        return result
                else:
                    result = {
                        "code": 3,
                        "desc": 'Failed to authentication'}
                    return result
