import json
from odoo import http, SUPERUSER_ID
from odoo.http import request

def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey

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

class getDataResUsers(http.Controller):
    
    @http.route('/api/testapi/get/listuser', type='json', auth="public", csrf=False)
    def getDataLocation(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                if request.httprequest.data:
                    values = json.loads(request.httprequest.data)
                print("\n\n\n TESTTTTTT",values)
                
                domain = []
                res_data = []
                datas = values

                if datas:
                    if not datas['id']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Id Not Found'}
                        return result
                    else:
                        domain += [('id', '=', datas['id'])]

                user_ids = request.env['res.users'].sudo().search(domain)
                for user_id in user_ids:
                    res_data.append({
                        'id': user_id.id,
                        'nama': user_id.name,
                    })
                page_number = int(request.httprequest.args.get('page'))  # Example page number
                if res_data:
                    # res_data = sorted(res_data, key=lambda x: x['id'])
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

                result = {
                    "code": 2,
                    "desc": "Success",
                    "total_pages": total_pages,
                    "page": page_number,
                    "data": paginated_result['data']
                    # "data": res_data
                }
                return result
            else:
                result = {"code": 4,
                          "desc": 'Access Denied'}
                return result
