from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError

import firebase_admin
from firebase_admin import credentials, messaging, db
import string
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from firebase_admin import credentials, auth
from firebase_admin.__about__ import __version__

from odoo.http import request
import requests
import base64
import binascii
import contextlib
import datetime
import hmac
import ipaddress
import itertools
import json
import logging
import os
import time
from hashlib import sha256

def cek_url(url):
    # untuk local
    path_local = "/opt/odoo14/custom-addons/mnc-bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"

    # untuk dev
    # path_dev = "/opt/odoo14/custom-addons/mnc-bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
    path_dev = "/home/devbcr/custom/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"

    # untuk prod
    path_prod = "/opt/odoo14/custom-addons/mnc-bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"

    cek_my_host = url
    if cek_my_host.find("localhost") > 0:
        path_run = path_local
        print("ini local host")
    elif cek_my_host.find("devbcr") > 0:
        path_run = path_dev
        print("ini devbcr host")
    elif cek_my_host.find("motionminers") > 0:
        path_run = path_prod
        print("ini motionminers host")
    else:
        path_run = path_local
        print("ini apa?")

    return path_run


class InheritLoginSh(models.Model):
    _inherit = 'res.users'
    # _description = 'Inherit Users'

    mobile_token = fields.Char("Mobile Token")

    # @api.model
    # def _update_last_login(self):
    #     # print("Cek Last Login")
    #     res = super(InheritLoginSh, self)._update_last_login()
    #     if len(firebase_admin._apps) == 0:
    #         cred = credentials.Certificate(
    #             cek_url(request.httprequest.host_url))
    #         default_app = firebase_admin.initialize_app(cred)
    #     uid = 'some-uid'
    #     custom_token = auth.create_custom_token(uid)
    #     # print(custom_token, "custom_token")
    #     if custom_token:
    #         self.env.user.write({'mobile_token': custom_token})
    #     return res

    # @tools.ormcache('sid')
    # def _compute_session_token(self, sid):
    #     """ Compute a session token given a session id and a user id """
    #     # retrieve the fields used to generate the session token
    #     session_fields = ', '.join(sorted(self._get_session_token_fields()))
    #     self.env.cr.execute("""SELECT %s, (SELECT value FROM ir_config_parameter WHERE key='database.secret')
    #                                 FROM res_users
    #                                 WHERE id=%%s""" % (session_fields), (self.id,))
    #     if self.env.cr.rowcount != 1:
    #         self.clear_caches()
    #         return False
    #     else:
    #         data_fields = self.env.cr.fetchone()
    #         # generate hmac key
    #         key = (u'%s' % (data_fields,)).encode('utf-8')
    #         # hmac the session id
    #         data = sid.encode('utf-8')
    #         h = hmac.new(key, data, sha256)
    #         # keep in the cache the token
    #
    #         # create token mobile from firebase create_custom_token
    #         if len(firebase_admin._apps) == 0:
    #             cred = credentials.Certificate(
    #                 cek_url(request.httprequest.host_url))
    #             default_app = firebase_admin.initialize_app(cred)
    #         uid = 'some-uid'
    #         custom_token = auth.create_custom_token(uid)
    #         print(custom_token, "custom_token")
    #         if custom_token:
    #             self.env.user.write({'mobile_token': custom_token})
    #         return h.hexdigest()

    # @tools.ormcache('sid')
    # def _compute_session_token(self, sid):
    #     res = super(InheritLoginSh, self)._compute_session_token(sid)
    #     if res:
    #         if not firebase_admin._apps:
    #             cred = credentials.Certificate(
    #                 cek_url(request.httprequest.host_url))
    #             default_app = firebase_admin.initialize_app(cred)
    #
    #         uid = 'some-uid'
    #         custom_token = auth.create_custom_token(uid)
    #         print(custom_token, "custom_token")
    #         # if custom_token:
    #         #     self.mobile_token = custom_token
    #
    #         print("inherit Login Men")
    #         return res
