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
import firebase_admin
from firebase_admin import credentials, messaging, db
import string
import random

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


# def excQueryFetchall(query):
#     request.env.cr.execute(query)
#     fetch_data = request.env.cr.fetchall()
#     return fetch_data
#
#
# def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
#     return ''.join(random.choice(chars) for _ in range(size))
#
# def cek_url(url):
#     # untuk local
#     path_local = "C:/odoo/odoo14/git_mnc/bcr/mnc-bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
#
#     # untuk dev
#     path_dev = "/home/devbcr/custom/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
#
#     # untuk prod
#     path_prod = "/home/devbcr/custom/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
#
#     cek_my_host = url
#
#     if cek_my_host.find("localhost") > 0:
#         path_run = path_local
#         print("ini local host")
#     elif cek_my_host.find("devbcr") > 0:
#         path_run = path_dev
#         print("ini devbcr host")
#     elif cek_my_host.find("motionminers") > 0:
#         path_run = path_prod
#         print("ini motionminers host")
#     else:
#         path_run = path_local
#         print("ini apa?")
#
#     return path_run
#
# def push_notification(title_value,message_value):
#
#     cred = credentials.Certificate(
#         cek_url(request.httprequest.host_url))
#     firebase_admin.initialize_app(cred, {
#         'databaseURL': 'https://motionminers-4b184-default-rtdb.firebaseio.com/'
#     })
#
#
#     topic = 'notification'
#     message = messaging.Message(
#         notification=messaging.Notification(
#             title=title_value,
#             body=message_value
#         ),
#         data=None,
#         topic=topic
#         # tokens=''
#     )
#
#     ref = db.reference('motion-mainers/')
#     if db.reference('motion-mainers/notification'):
#         notif = ref.child('notification')
#         notif.update(
#             {
#                 id_generator(): {
#                     'title': title_value,
#                     'message': message_value
#                 }
#             }
#         )
#     else:
#         notif = ref.child('notification')
#         notif.set(
#             {
#                 id_generator(): {
#                     'title': title_value,
#                     'message': message_value
#                 }
#             }
#         )
#     print('Push Notification Message', message)
#     response = messaging.send(message)
#     print('Push Notification', response)
#
#     return response

class BcrInterfaceNotification(http.Controller):

    def search_usr_validation_by_model(self, id_parent_model, id_model, state):
        src_user = request.env["validation.plan"].search([(id_parent_model, "=", int(id_model)), ("validation_type_id.code", "=", state)])
        if src_user:
            print(src_user,"src_user")
            return src_user
        #     print(src_user.user_id.login)
        #     return src_user.user_id.login
        # else:
        #     return False

    @http.route('/api/notification/person', type='json', auth="none")
    def getData(self, values=None):
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

                    if not datas['model']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Model Not Found'}
                        return result

                    if not datas['state']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'State Not Found'}
                        return result

                res = request.env['push.notification'].sudo().push_notification_scheduler_person(datas['login'], datas["model"], datas["state"])

                return res


    # old script

    @http.route('/api/test/notification', type='json', auth="none")
    def getData(self, values=None):
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
                    if not datas['title']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Message Not Found'}
                        return result

                    if not datas['message']:
                        result = {
                            "code": 3,
                            "data": [],
                            "desc": 'Message Not Found'}
                        return result

                token_richard = "eAyFzvX6Q-ezoNCerePPAV:APA91bHfAkI7Z1B4dLYYN-I2ICa5j6WRXVLqg1I6jz4HDYJX6-dLTReeBdXz2TQaG80bIlfzoiNeKO17TeALMwzf1S6hDW_HBpdFwYpi5P5eWAOL5BPxdfvcpxGBDSh6HJAzz7y_Y8SC"
                server_token = "AAAAXp_hEig:APA91bEBR11yIYRKenwhV2cp4aDS7yzoWiJW2VH9pwuiQxWRC430TECPDqDm9PzzxGwLDyutaZrMliGH_l4XCQ3wHjCXTSQvqPrO4I12210p2n3KWuCEpu0NO2qNC8aMjTRK3KLbaTbH"

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + server_token,
                }

                body = {
                    'notification': {'title': datas['title'],
                                     'body': datas['message']
                                     },
                    'to':
                        token_richard,
                    'priority': 'high',
                    #   'data': dataPayLoad,
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))
                print(response.status_code)

