import json
from odoo import http, SUPERUSER_ID, _
from odoo.http import request
from odoo import fields


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


def get_attachment(res_id, ttype, thumbnail=False):
    url = request.httprequest.host_url
    attach_obj = request.env['ir.attachment']
    model = False
    image_url = ""
    if ttype == 'banner':
        model = 'mncei.banner'
        fields = thumbnail
        print("=====Attachment=====")
        print(fields)
        domain = [('res_id', '=', res_id.id), ('res_model', '=', model), ('res_field', '=', fields)]
        print(domain)
        attachment_id = attach_obj.search(domain, limit=1)
        if attachment_id:
            image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(attachment_id.id))
    elif ttype == 'news':
        model = 'mncei.news'
        domain = [('res_id', '=', res_id.id), ('res_model', '=', model)]
        if thumbnail:
            domain += [('res_field', '=', 'thumb_img')]
        else:
            domain += [('res_field', '=', 'news_img')]
        attachment_id = attach_obj.search(domain, limit=1)
        if attachment_id:
            image_url = _("%sweb/image?model=ir.attachment&id=%s&field=datas") % (url, str(attachment_id.id))
    return image_url


class GetDataBanner(http.Controller):
    @http.route('/api/banner/listed', type='json', auth="public", methods=['GET'])
    def getDataBanner(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                today = fields.Date.today()
                banner_ids = request.env['mncei.banner'].search([('date_start', '<=', today), ('date_end', '>=', today), ('state', '=', 'release')])
                if banner_ids:
                    for banner_id in banner_ids:
                        # banner_img = _("%sweb/image?model=mncei.banner&id=%s&field=banner_img") % (url, str(banner_id.id))
                        banner_img_url = get_attachment(banner_id, 'banner', thumbnail='banner_img')
                        detail_img_url = get_attachment(banner_id, 'banner', thumbnail='detail_img')

                        print("SSSSSSSSSSSSSSSSSSs")
                        print(banner_img_url)
                        print(detail_img_url)
                        res_data.append({
                            'id': banner_id.id,
                            'title': banner_id.title or "",
                            'description': banner_id.description or "",
                            'date_start': banner_id.date_start,
                            'date_end': banner_id.date_end,
                            'img': detail_img_url or "",
                            'img_url': banner_img_url or "",
                            'link_url': banner_id.link or "",
                        })
                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "desc": "Failed",
                        "data": "Banner is empty"
                    }
                    return result
            else:
                result = {"code": 4,
                          "desc": 'Access Denied'}
                return result


class GetDataNews(http.Controller):
    @http.route('/api/news/listed', type='json', auth="public", methods=['GET'])
    def getDataNews(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                res_data = []
                today = fields.Date.today()
                news_ids = request.env['mncei.news'].search([('date_start', '<=', today), ('date_end', '>=', today), ('state', '=', 'release')])
                if news_ids:
                    for news_id in news_ids:
                        thumnail_img_url = get_attachment(news_id, 'news', thumbnail=True)
                        news_img_url = get_attachment(news_id, 'news')
                        res_data.append({
                            'id': news_id.id,
                            'title': news_id.title,
                            'description': news_id.description or "",
                            'thumbnail': news_id.thumbnail or "",
                            'thumbnail_img': "",
                            'thumbnail_img_url': thumnail_img_url,
                            'img': "",
                            'img_url': news_img_url,
                            'date_start': news_id.date_start,
                            'date_end': news_id.date_end,
                        })
                    result = {
                        "code": 2,
                        "desc": "Success",
                        "data": res_data
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "desc": "Failed",
                        "data": "News is empty"
                    }
                    return result
            else:
                result = {"code": 4,
                          "desc": 'Access Denied'}
                return result
