from odoo import api, fields, models, _
from odoo.exceptions import UserError

import firebase_admin
from firebase_admin import credentials, messaging, db
import string
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo.http import request
import requests
import json
# =============================
# Change rules token
from google.oauth2 import service_account
import google.auth.transport.requests
# =============================

from .query_notification import BcrQeuryNotif

import logging
_logger = logging.getLogger(__name__)

code_models = {
    'act.production': 'AP',
    'act.stockroom': 'AS',
    'act.barging': 'AB',
    'act.delay': 'AD',
    'act.hauling': 'AH',
    'planning.hauling': 'PH',
    'planning.barging': 'PB',
    'planning.production': 'PP',
}


def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def conv_time_float(value):
    vals = value.split(':')
    t, hours = divmod(float(vals[0]), 24)
    t, minutes = divmod(float(vals[1]), 60)
    minutes = minutes / 60.0
    return hours + minutes


def excQueryFetchall(query):
    request.env.cr.execute(query)
    fetch_data = request.env.cr.fetchall()
    return fetch_data


def cek_url(url):
    # untuk local
    path_local = "C:/workspace/mnc_bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
    # untuk dev
    path_dev = "/home/devbcr/custom/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
    # untuk prod
    path_prod = "/opt/odoo14/custom-addons/mnc-bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
    # 192
    path_energy = "/home/ubuntu/custom/mnc-bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
    # Check URL
    cek_my_host = url
    if cek_my_host.find("localhost") > 0:
        path_run = path_local
        print("ini local host")
    elif cek_my_host.find("devbcr") > 0:
        path_run = path_dev
        print("ini devbcr host")
    elif cek_my_host.find("mncminers") > 0:
        path_run = path_prod
        print("ini motionminers host")
    elif cek_my_host.find("192.168.12.20") > 0:
        path_run = path_energy
        print("ini path server Energy")
    else:
        path_run = path_local
        print("ini apa?")

    return path_run


def cek_time_max():
    # time_max_message_par = request.env['ir.config_parameter'].sudo().get_param(
    #     'bcr.time_max_scheduler_message_notification')
    time_max_message_par = request.env['push.notification.setting'].sudo().search([("code", "=", "PNTM01"), ("status", "=", True)])

    if not time_max_message_par:
        print("time_max_message_par not enable")
        return False

    time_odoo = fields.Datetime.now() + relativedelta(hours=7)
    time_odoo = time_odoo.strftime("%H:%M")

    time_max_message_par = conv_time_float(time_max_message_par[0].value)
    time_odoo = conv_time_float(time_odoo)

    if time_odoo <= time_max_message_par:
        return True
    else:
        return False


def message_total(kode, total, model, message_par):
    model = model.replace(".", " ")
    if kode == "message_notification_review":
        message_par = message_par.replace("[[total]]", str(total) + " Review").replace("[[model]]", str(model))

    elif kode == "message_notification_approve":
        message_par = message_par.replace("[[total]]", str(total) + " Approve").replace("[[model]]", str(model))

    return message_par


def message_code(kode, code_activity, model, message_par):
    model = model.replace(".", " ")
    if kode == "message_notification_review":
        message_par = message_par.replace("[[state]]", "Review").replace("[[model]]", str(model)).replace("[[code_activity]]", str(code_activity))

    elif kode == "message_notification_approve":
        message_par = message_par.replace("[[state]]", "Approve").replace("[[model]]", str(model)).replace("[[code_activity]]", str(code_activity))

    return message_par


def firebase_json(url):
    # untuk local
    path_local = "C:/workspace/mnc_bcr/bcr_api_sh/static/js/firebase_master.json"
    # untuk prod
    path_prod = "/opt/odoo14/custom-addons/mnc-bcr/bcr_api_sh/static/js/firebase_master.json"
    # 192
    path_energy = "/home/ubuntu/custom/mnc-bcr/bcr_api_sh/static/js/firebase_master.json"
    # Check URL
    cek_my_host = url
    if cek_my_host.find("localhost") > 0:
        path_run = path_local
        print("ini local host")
    elif cek_my_host.find("mncminers") > 0:
        path_run = path_prod
        print("ini motionminers host")
    elif cek_my_host.find("192.168.12.20") > 0:
        path_run = path_energy
        print("ini path server Energy")
    else:
        path_run = path_local
        print("ini apa?")

    return path_run


def get_scoopes():
    scoopes_url = request.env['ir.config_parameter'].sudo().get_param('scoopes_url')
    return scoopes_url


def get_token_firebase(path):
    credentials = service_account.Credentials.from_service_account_file(
      path, scopes=[get_scoopes()])
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token


# Method untuk push notif
def push_notification(topic_value, title_value, message_par, mobile_token, login, to_review=False, code=False):
    # Cek url untuk file json
    if not firebase_admin._apps:
        cred = credentials.Certificate(
            cek_url(request.httprequest.host_url))
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://motionminers-4b184-default-rtdb.firebaseio.com/'
        })
    message_value = message_par
    # Mobile token di dapat dari user
    # ada api mobile token yang dikirim dari mobile
    if mobile_token:
        # =====================
        # Token Server notifikasi
        path_firebase = firebase_json(request.httprequest.host_url)
        server_token = get_token_firebase(path_firebase)
        # =====================
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + server_token,
        }
        body = {
            "message": {
                "token": mobile_token,
                "notification": {
                    "title": title_value,
                    "body": message_value
                },
                "data": {
                    'action': 'REVIEW',
                    'menu': code.upper()
                }
            }
        }
        # body = {
        #     'notification': {
        #         'title': title_value,
        #         'body': message_value
        #     },
        #     'to': mobile_token,
        #     'priority': 'high',
        # }
        # print("======Body=======")
        # print(body)
        # if to_review:
        #     body.update({
        #         'data': {
        #             'action': "REVIEW",
        #             'menu': code
        #         }
        #     })
        # Send notification to mobile
        print("========After======")
        print(body)
        response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))
        print(response.status_code)
        # Create Realtime DB
        ref = db.reference('motion-mainers/')
        if db.reference('motion-mainers/notification'):
            notif = ref.child('notification')
            notif.update({
                id_generator(): {
                    'title': title_value,
                    'message': message_value,
                    'login': login,
                    'mobile_token': mobile_token,
                }
            })
        else:
            notif = ref.child('notification')
            notif.set({
                id_generator(): {
                    'title': title_value,
                    'message': message_value,
                    'login': login,
                    'mobile_token': mobile_token,
                }
            })
        print('Push Notification Message', message_value)
        result = {
            "code": 2,
            "desc": 'Success'}
        return result
    else:
        result = {
            "code": 3,
            "desc": 'failed'}
        return result


class SettingPushNotification(models.Model):
    _name = 'push.notification.setting'
    _description = 'Push Notification Setting'

    title = fields.Char(string="Title")
    code = fields.Char(string="Code", readonly=True)
    value = fields.Char(string="Value")
    status = fields.Boolean(string="Status")
    description = fields.Text(string="Description")
    # allow_group_ids = fields.Many2many('res.groups', string="Allow Groups")
    not_allowed_company_ids = fields.Many2many('res.company', string="Not Allowed Company")


class PushNotification(models.Model):
    _name = 'push.notification'
    _description = 'Push Notification'
    _order = 'create_date desc'

    user = fields.Many2one(comodel_name="res.users", string="User")
    company = fields.Many2one(comodel_name="res.company", string="Company")
    topic = fields.Char(string="Topic")
    title = fields.Char(string="Title")
    message = fields.Char(string="Message")
    code = fields.Char('Code')
    action = fields.Char('Actions')
    res_id = fields.Integer('Res ID', store=True)
    is_read = fields.Boolean('Read', default=False)

    def count_tes(self, id_user, model, state):
        res = self.env[model].search([("state", "=", state)]).validation_plan.filtered(
                lambda x: x.user_id.id == id_user and x.validation_type_id.code == state)
        if res:
            return len(res)
        else:
            return 0

    def push_notification(self, login, model, state, code_activity, to_review=False):
        src_id = self.env["res.users"].search([("login", "=", login)]).id
        mobile_token = self.env["res.users"].search([("login", "=", login)]).mobile_token
        ct = self.count_tes(src_id, model, state)
        # message_par = request.env['ir.config_parameter'].sudo().get_param('bcr.scheduler_message_notification')
        message_par = request.env['push.notification.setting'].sudo().search([("code", "=", "PNMP01"), ("status", "=", True)])
        # if ct > 0:
        if mobile_token:
            if not message_par:
                print(message_par, "message_par not enable")
                return True

            if state == "review":
                message_par = message_code("message_notification_review", code_activity, model, message_par[0].value)
                # message_par = message_total("message_notification_review", ct, model, message_par[0].value)
            elif state == "approve":
                message_par = message_code("message_notification_approve", code_activity, model, message_par[0].value)
                # message_par = message_total("message_notification_approve", ct, model, message_par[0].value)
            else:
                result = {
                    "code": 4,
                    "desc": 'State in Odoo Not Found'}
                return result

            topic = 'notification'
            title_value = "notification person"
            code = code_models.get(model)
            if to_review and code:
                response = push_notification(topic, title_value, message_par, mobile_token, login, to_review=True, code=code)
                action = 'review'
            else:
                response = push_notification(topic, title_value, message_par, mobile_token, login, code='OV')
                code = 'OV'
            # After get response
            if response:
                self.env["push.notification"].create({
                    "user": src_id,
                    "topic": topic,
                    "title": title_value,
                    'code': code,
                    'action': action,
                    "message": message_par
                })
            return response
        else:
            return True

    # Message replace dari Notification Setting
    def message_notif_s(self,message, login, iup, sub_activity, date_stop, date_start, plan, aktual, ach, data_remark_date, remark):
        message_replace = message.replace("[[login]]", str(login)).replace("[[sub_activity]]", str(sub_activity)).replace("[[iup]]", str(iup)).replace("[[date_stop]]", str(date_stop)).replace("[[date_start]]", str(date_start)).replace("[[plan]]", str(plan)).replace("[[aktual]]", str(aktual)).replace("[[ach]]", str(ach)).replace("[[remark]]", str(remark)).replace("[[data_remark_date]]", str(data_remark_date))
        return message_replace

    # Method Get Push notification
    def push_notification_s(self, code, login, tipe, iup, sub_activity, iup_id, date_stop, date_start, plan, aktual, ach, data_remark_date, remark):
        src_id = self.env["res.users"].search([("login", "=", login)]).id
        mobile_token = self.env["res.users"].search([("login", "=", login)]).mobile_token
        if code == 1:
            # 1 Tercapai/0 Tidak Tercapai
            if not tipe:
                message_not_achieve = request.env['push.notification.setting'].sudo().search(
                    [("code", "=", "PNMD01"), ("status", "=", True)])
                if not message_not_achieve:
                    return False
                cek_not_allow_iup_ids = message_not_achieve[0].not_allowed_company_ids
                for not_allow_iup in cek_not_allow_iup_ids:
                    if not_allow_iup.id == iup_id:
                        return False
                message_not_achieve = self.message_notif_s(message_not_achieve[0].value,login, iup, sub_activity, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                message_par = message_not_achieve
            else:
                message_achieve = request.env['push.notification.setting'].sudo().search(
                    [("code", "=", "PNMD02"), ("status", "=", True)])
                if not message_achieve:
                    return False
                cek_not_allow_iup_ids = message_achieve[0].not_allowed_company_ids
                for not_allow_iup in cek_not_allow_iup_ids:
                    if not_allow_iup.id == iup_id:
                        return False
                message_achieve = self.message_notif_s(message_achieve[0].value,login, iup, sub_activity, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                message_par = message_achieve
            print("1")
        elif code == 2:
            if not tipe:
                message_not_achieve = request.env['push.notification.setting'].sudo().search(
                    [("code", "=", "PNMW01"), ("status", "=", True)])
                if not message_not_achieve:
                    return False
                cek_not_allow_iup_ids = message_not_achieve[0].not_allowed_company_ids
                for not_allow_iup in cek_not_allow_iup_ids:
                    if not_allow_iup.id == iup_id:
                        return False
                message_not_achieve = self.message_notif_s(message_not_achieve[0].value,login, iup, sub_activity, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                message_par = message_not_achieve
            else:
                message_achieve = request.env['push.notification.setting'].sudo().search(
                    [("code", "=", "PNMW02"), ("status", "=", True)])
                if not message_achieve:
                    return False
                cek_not_allow_iup_ids = message_achieve[0].not_allowed_company_ids
                for not_allow_iup in cek_not_allow_iup_ids:
                    if not_allow_iup.id == iup_id:
                        return False
                message_achieve = self.message_notif_s(message_achieve[0].value,login, iup, sub_activity, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                message_par = message_achieve
            print("2")
        elif code == 3:
            if not tipe:
                message_not_achieve = request.env['push.notification.setting'].sudo().search(
                    [("code", "=", "PNMM01"), ("status", "=", True)])
                if not message_not_achieve:
                    return False
                cek_not_allow_iup_ids = message_not_achieve[0].not_allowed_company_ids
                for not_allow_iup in cek_not_allow_iup_ids:
                    if not_allow_iup.id == iup_id:
                        return False
                message_not_achieve = self.message_notif_s(message_not_achieve[0].value,login, iup, sub_activity, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                message_par = message_not_achieve
            else:
                message_achieve = request.env['push.notification.setting'].sudo().search(
                    [("code", "=", "PNMM02"), ("status", "=", True)])
                if not message_achieve:
                    return False
                cek_not_allow_iup_ids = message_achieve[0].not_allowed_company_ids
                for not_allow_iup in cek_not_allow_iup_ids:
                    if not_allow_iup.id == iup_id:
                        return False
                message_achieve = self.message_notif_s(message_achieve[0].value,login, iup, sub_activity, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                message_par = message_achieve
            print("3")

        topic = 'notification'
        title_value = "notification schedule"
        response = push_notification(topic, title_value, message_par, mobile_token, login, code='OV')
        if response:
            self.env["push.notification"].create({
                "user": src_id,
                "company": iup_id,
                "topic": topic,
                "title": title_value,
                "code": "OV",
                "action": "OV",
                "message": message_par
            })
        return response

    # Function pada schedule action, u/ push notifikasi
    # Schedule > Method (push_notification_scheduler) ? code > Method (push_notification_s) > message get pada parameter log > method(message_notif_s)
    def push_notification_scheduler(self, code):
        if code == 1:
            ex_data = excQueryFetchall(BcrQeuryNotif.QueryNotifDaily(self))
            for data in ex_data:
                data_remark_date = data[0]
                date_start = data[1]
                date_stop = data[2]
                iup_id = data[3]
                iup = data[4]
                sub_activity = data[5]
                plan = data[6]
                aktual = data[7]
                ach = data[8]
                login = data[9]
                tipe = data[10]
                remark = data[11]
                res = self.push_notification_s(code, login, tipe, iup, sub_activity, iup_id, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                if not res:
                    print("ga kirim daily")
                print(data, "data daily")
            print("schedule daily")
        elif code == 2:
            ex_data = excQueryFetchall(BcrQeuryNotif.QueryNotifWeekly(self))
            for data in ex_data:
                data_remark_date = data[0]
                date_start = data[1]
                date_stop = data[2]
                iup_id = data[3]
                iup = data[4]
                sub_activity = data[5]
                plan = data[6]
                aktual = data[7]
                ach = data[8]
                login = data[9]
                tipe = data[10]
                remark = data[11]
                res = self.push_notification_s(code, login, tipe, iup, sub_activity, iup_id, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                if not res:
                    print("ga kirim weekly")
                print(data, "data weekly")
            print("schedule weekly")
        elif code == 3:
            ex_data = excQueryFetchall(BcrQeuryNotif.QueryNotifMonthly(self))
            for data in ex_data:
                data_remark_date = data[0]
                date_start = data[1]
                date_stop = data[2]
                iup_id = data[3]
                iup = data[4]
                sub_activity = data[5]
                plan = data[6]
                aktual = data[7]
                ach = data[8]
                login = data[9]
                tipe = data[10]
                remark = data[11]
                res = self.push_notification_s(code, login, tipe, iup, sub_activity, iup_id, date_stop, date_start, plan, aktual, ach, data_remark_date, remark)
                if not res:
                    print("ga kirim monthly")
                print(data, "data monthly")
            print("schedule monthly")
        else:
            result = {
                "code": 4,
                "desc": 'Time has exceeded business hours'}
            return result

    def push_notification_person(self, login, model, state, code_activity):
        if cek_time_max():
            result = self.push_notification(login, model, state, code_activity, to_review=True)
            return result
        else:
            result = {
                "code": 4,
                "desc": 'Time has exceeded business hours'}
            return result
