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

import babel.messages.pofile
import base64
import copy
import datetime
import functools
import glob
import hashlib
import io
import itertools
import jinja2
import json
import logging
import operator
import os
import re
import sys
import tempfile

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from collections import OrderedDict, defaultdict, Counter
from werkzeug.urls import url_encode, url_decode, iri_to_uri
from lxml import etree
import unicodedata


import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_module_path, get_resource_path
from odoo.tools import image_process, topological_sort, html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlsxwriter, file_open
from odoo.tools.safe_eval import safe_eval, time
from odoo import http, tools
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.models import check_method_name
from odoo.service import db, security
from odoo.addons.web.controllers.main import Session
from odoo.exceptions import AccessDenied

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


class BcrInterface(http.Controller):

    @http.route('/api/account/forgot_password', type='json', auth="none")
    def getDataForgetPassword(self, values=None):
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
                if datas:
                    if not datas['login']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Login Not Found'}
                        return result

                    login = datas['login']
                    user = request.env['res.users'].sudo()
                    print("SSSSSSSSSSSSSSSSS")
                    print(user)
                    send_email = user.with_context(mobile=True).reset_password(login)
                    get_token = user.search([("login", "=", datas["login"])])
                    print(send_email)
                    print(get_token)
                    token = get_token[0].partner_id.signup_token
                    result = {
                        "code": 2,
                        "data":
                            {
                                "login": login,
                                "token": token
                            },
                        "desc": "Success"
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "desc": 'Failed to authentication'}
                    return result

            else:
                result = {"code": 4,
                          "desc": 'Access Denied'}
                return result

    @http.route('/api/account/change_password', type='json', auth="none")
    def getDataChangePassword(self, values=None):
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
                if datas:
                    if not datas['token']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Token Not Found'}
                        return result

                    if not datas['new_password']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Password Not Found'}
                        return result

                    if not datas['confirm_password']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Confirm Password Not Found'}
                        return result

                    cek_token = request.env['res.partner'].sudo().search([("signup_token", "=", datas['token'])])
                    if cek_token:
                        user = request.env['res.users'].sudo().search([("partner_id", "=", cek_token[0].id)])
                        new_password = datas["new_password"]
                        confirm_password = datas["confirm_password"]
                        if new_password != confirm_password:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'Password Not Matching'}
                            return result
                        else:
                            user.write({'password': new_password})
                            result = {
                                "code": 2,
                                "data": {
                                    "new_password": new_password
                                },
                                "desc": 'Success'}
                            return result

                    else:
                        result = {
                            "code": 3,
                            "desc": 'Failed Token'}
                        return result
            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
                return result

    @http.route('/api/account/detail/get', type='json', auth="user")
    def getDataAccount(self, values=None):
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
                    access_bcr_process = []
                    access_bcr_master = []
                    type_user = ""
                    type_admin = False
                    # search domain
                    if datas:
                        if not datas['login']:
                            result = {
                                "code": 3,
                                "data": [],
                                "desc": 'Login Not Found'}
                            return result

                        for group in user.groups_id:
                            if group.category_id.name == "BCR Master":
                                access_bcr_master.append({
                                    "id": group.id,
                                    "name": group.name
                                }
                                )

                            if group.category_id.name == "BCR Process #1":
                                access_bcr_process.append({
                                    "id": group.id,
                                    "name": group.name
                                })

                                if group.name == "All Review":
                                    type_user = type_user + "Reviewer"
                                elif group.name == "All Approve":
                                    type_user = type_user + "Approver"

                                if group.name == "Admin":
                                    type_admin = True

                        if type_user == "ApproverReviewer" or type_user == "ReviewerApprover":
                            type_user = "Reviewer & Approver"
                        if type_user == "":
                            if type_admin:
                                type_user = "Report Viewer"
                            else:
                                type_user = "Not Allow Access"

                        allowed_companies = []
                        for comp in user.company_ids:
                            code_comp = request.env['master.bisnis.unit'].sudo().search(
                                [('bu_company_id', '=', comp.id)], limit=1).code
                            if code_comp:
                                allowed_companies.append({
                                    'id': comp.id,
                                    'code': code_comp,
                                    'name': comp.name
                                })

                        result = {
                            "code": 2,
                            "data": {
                                "name": user.name,
                                "login": user.login,
                                "type_user": type_user or "",
                                "tipe_user": user.tipe_user or "",
                                "mobile_user": user.is_login_mobile or False,
                                "mobile_token": user.mobile_token or "",
                                "user_companies": {
                                    'current_company': [
                                        {
                                            'id': user.company_id.id,
                                            'code': request.env['master.bisnis.unit'].sudo().search(
                                                [('bu_company_id', '=', user.company_id.id)], limit=1).code,
                                            'name': user.company_id.name
                                        }],
                                    'allowed_companies': allowed_companies,
                                    'access_bcr_master': access_bcr_master,
                                    'access_bcr_process': access_bcr_process
                                },

                            },
                            "desc": "Success"
                        }

                        return result

                else:
                    result = {
                        "code": 3,
                        "desc": 'Failed to authentication'}
                    return result

        else:
            result = {"code": 4,
                      "desc": 'Access Denied'}
            return result

    @http.route('/api/account/change_token_mobile', type='json', auth="user")
    def changeTokenMobile(self, values=None):
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
                print(datas, "datas")
                if datas:
                    if not datas['token']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Token Not Found'}
                        return result

                user = request.env['res.users'].sudo().search([('id', '=', request.env.user.id)])
                res = user.write({
                    'mobile_token': datas['token']
                })
                if res:
                    result = {
                        "code": 2,
                        "token": datas['token'],
                        "desc": "Success"
                    }
                    return result
                else:
                    result = {
                        "code": 3,
                        "desc": 'Failed'}
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
                    vals = []
                    # if datas:
                    #     if not datas['iup']:
                    #         result = {
                    #             "code": 3,
                    #             "data": [],
                    #             "desc": 'IUP Not Found'}
                    #         return result

                    obj = request.env['push.notification'].sudo()
                    if len(datas['iup']) > 0:
                        data_log = obj.search(
                            [('user', '=', user.id), ('company', 'in', datas['iup'])])
                    else:
                        data_log = obj.search(
                            [('user', '=', user.id)], order='create_date desc')

                    if data_log:
                        for x_data in data_log:
                            obj = {
                                'create_date': x_data.create_date or "0000-00-00",
                                'company': x_data.company.name or "All",
                                'user': x_data.user.name or 0,
                                'title': x_data.title or "",
                                'code': x_data.code or "OV",
                                'action': x_data.action or "OV",
                                'message': x_data.message or "",
                            }
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
                            "data": [],
                            "desc": "Data Not Found"
                        }
                        return result
                else:
                    result = {
                        "code": 3,
                        "desc": 'Failed to authentication'}
                    return result
