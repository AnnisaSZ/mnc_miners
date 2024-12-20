from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

from odoo.addons.mnc_attendance.controllers.main import remove_seconds

import logging
import json
import requests

TIMEOUT = 20

_logger = logging.getLogger(__name__)


def get_late_key(self):
    late_key = self.env['ir.config_parameter'].sudo().get_param('Late_Key')
    return late_key


class QontakAuth(models.Model):
    _name = "qontak.auth"
    _rec_name = 'username'

    username = fields.Char("Username", store=True)
    password = fields.Char("Password")
    client_id = fields.Char("Client ID", store=True)
    client_secret = fields.Char("Client Secret")
    # Token
    token = fields.Char('Token')
    refresh_token = fields.Char('Refresh Token')
    # Channel
    channel_ids = fields.One2many('qontak.channel', 'auth_id', string="Channels")
    template_ids = fields.One2many('qontak.template', 'auth_id', string="Templates")

    @api.model
    def _do_request(self, uri, params={}, headers={}, type='POST'):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('whatsapp_base_url')
        try:
            if type.upper() in ('GET', 'DELETE'):
                res = requests.request(
                    type.lower(), base_url + uri, params=params, headers=headers, timeout=TIMEOUT)
            elif type.upper() in ('POST', 'PATCH', 'PUT'):
                res = requests.request(
                    type.lower(), base_url + uri, data=params, headers=headers, timeout=TIMEOUT)
            else:
                raise Exception(
                    _('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!') % (type))
            # res.raise_for_status()
            status = res.status_code

            if int(status) in (204, 404):  # Page not found, no response
                response = False
            else:
                response = res.json()
        except requests.HTTPError as error:
            if error.response.status_code in (204, 404):
                status = error.response.status_code
                response = ""
            else:
                _logger.exception("Bad request : %s !", error.response.content)
                if error.response.status_code in (400, 401, 403, 410, 422):
                    raise error
                raise self.env['res.config.settings'].get_config_warning(
                    _("Something went wrong with your request to whatsapp Qontak"))
        return (status, response)

    # login and refresh token
    def action_refresh_token(self):
        uri = '/oauth/token'
        headers = {'Content-Type': "application/json"}
        data = {
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        status, response = self._do_request(uri, json.dumps(data), headers, 'POST')
        if status != 201:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _("Failed Refresh Token"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            self.token = response['access_token']
            self.refresh_token = response['refresh_token']
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Update Token successfully"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

    # Get Channel
    def action_get_channel(self):
        uri = '/api/open/v1/integrations?target_channel=wa&limit=10'
        headers = {'Authorization': _("Bearer %s") % (self.token)}
        data = {}
        status, response = self._do_request(uri, json.dumps(data), headers, 'GET')
        if status != 200:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _("Failed get channel"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            channel_list = []
            for data in response['data']:
                channel_list.append((0, 0, {
                    'qontak_id': data['id'],
                    'target_channel': data['target_channel'],
                    'account_name': data['settings']['account_name'],
                    'account_number': data['settings']['phone_number'],
                    'is_active': data['is_active'],
                }))
            if self.channel_ids:
                for channel in self.channel_ids:
                    channel.unlink()
            # self.channel_ids = False
            self.channel_ids = channel_list
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Get Channel successfully"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

    # Get Template
    def action_get_template(self):
        uri = '/api/open/v1/templates/whatsapp'
        headers = {'Authorization': _("Bearer %s") % (self.token)}
        data = {}
        status, response = self._do_request(uri, json.dumps(data), headers, 'GET')
        if status != 200:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _("Failed get templates"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            temp_list = []
            for data in response['data']:
                temp_list.append((0, 0, {
                    'qontak_id': data['id'],
                    'organization_id': data['organization_id'],
                    'name': data['name'],
                    'body': data['body'],
                    'status': data['status'],
                    'category': data['category'],
                }))
            if self.template_ids:
                for template in self.template_ids:
                    template.unlink()
            # self.template_ids = False
            self.template_ids = temp_list
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Get templates successfully"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

    def get_body(self, params, param_count):
        print("XXXXXXXXXXXXXXXX00")
        print(params)
        print(param_count)
        body = []
        i = 0
        while i < param_count:
            # key = i + 1
            try:
                name = params[i]['name']
            except:
                name = '-'

            print("XXXXXXXXXXXXXXXX01")
            body.append({
                "key": str(i),
                "value": _("name_%s") % (str(i)),
                "value_text": name
            })
            i += 1
        return body

    def format_number(self, number):
        # Jika nomor dimulai dengan '+62', hapus '+' untuk mendapatkan format yang diinginkan
        if number.startswith('+62'):
            return number[1:]
        # # Jika nomor dimulai dengan '0', ganti dengan '62'
        elif number.startswith('0'):
            return '62' + number[1:]
        # # Jika sudah dalam format '62', biarkan tetap
        elif number.startswith('62'):
            return number
        else:
            return '62' + number

    def get_datas(self, user_id, template_id, channel_id, datas):
        template_txt = template_id.body
        # get total variable
        # ===================================
        left_braces_count = template_txt.count('{{')
        right_braces_count = template_txt.count('}}')
        # Total pairs of '{{}}'
        pairs_count = min(left_braces_count, right_braces_count)
        # ===================================
        number = self.format_number(user_id.mncei_employee_id.no_wa)
        format_dates = fields.Date.today().strftime("%d%m%Y")
        values = _("?date=%s&uid=%s") % (format_dates, user_id.id)
        data = {
            "to_number": number,
            "to_name": user_id.mncei_employee_id.nama_lengkap,
            "message_template_id": template_id.qontak_id,
            "channel_integration_id": channel_id.qontak_id,
            "language": {
                "code": "id"
            },
            "parameters": {
                "body": self.get_body(datas, pairs_count),
                "buttons": [
                    {
                        "index": "0",
                        "type": "url",
                        "value": values
                    }
                ]
            }
        }
        return data

    def send_notify(self):
        auth_id = self.env['qontak.auth'].search([('token', '!=', False)], limit=1)
        auth_id.action_send_direct()
        return

    # Send WA Direct
    def action_send_direct(self):
        # Logging Obj
        uri = '/api/open/v1/broadcasts/whatsapp/direct'
        headers = {
            'Authorization': _("Bearer %s") % (self.token),
            'Content-Type': "application/json",
        }
        late_key = get_late_key(self)
        template_id = self.env['qontak.template'].search([('qontak_id', '=', late_key)], limit=1)
        channel_id = self.env['qontak.channel'].search([('qontak_id', '=', 'c768bfd7-b7aa-4e48-9eca-da02e612b57e')], limit=1)
        recipient_id = self.env['miners.recipient'].search([], limit=1)
        # BOD
        for user_id in recipient_id.bod_response_uids:
            if user_id.mncei_employee_id:
                if user_id.mncei_employee_id.no_wa:
                    res_data = self.send_user(user_id)
                    if len(res_data) >= 1:
                        data = self.get_datas(user_id, template_id, channel_id, res_data)
                        res_datas = {
                            'uri': uri,
                            'data': data,
                            'headers': headers,
                        }
                        self.env["queue.job"].with_delay(
                            priority=None,
                            max_retries=None,
                            channel=None,
                            description=f"WA: Send notify late to {user_id.login}",
                        )._to_send_whatsapp(res_datas, user_id)
                else:
                    self.create_logging(user_id, "404", "Please Input No whatsapp")
        # Department Head
        for dept_id in recipient_id.department_recipient_ids:
            print("SSSSSSSSSSSSSSSSSSSSSSS")
            for user_id in dept_id.user_ids:
                print("SSSSSSSSSSSSSSSSSSSSSSS00")
                if user_id.mncei_employee_id:
                    print("SSSSSSSSSSSSSSSSSSSSSSS01")
                    if user_id.mncei_employee_id.no_wa:
                        res_data = self.send_user(user_id)
                        print(res_data)
                        if len(res_data) >= 1:
                            data = self.get_datas(user_id, template_id, channel_id, res_data)
                            res_datas = {
                                'uri': uri,
                                'data': data,
                                'headers': headers,
                            }
                            self.env["queue.job"].with_delay(
                                priority=None,
                                max_retries=None,
                                channel=None,
                                description=f"WA: Send notify late to {user_id.login}",
                            )._to_send_whatsapp(res_datas, user_id)
                    else:
                        self.create_logging(user_id, "404", "Please Input No whatsapp")
        return

    def send_user(self, user_id):
        res_data = []
        teams = user_id.mncei_employee_id.get_all_children_of_parent()
        for employee_id in teams:
            domain = [('mncei_employee_id', '=', employee_id.id)]
            # Get Today
            time_today = fields.Datetime.now()
            date_check_in = time_today - timedelta(hours=7)
            date_check_out = (time_today + timedelta(days=1)) - timedelta(hours=7)
            # Get Attendance
            domain_ci = domain + [('check_in', '>=', date_check_in), ('check_in', '<=', date_check_out)]
            attendance_ci = self.env['hr.attendance'].sudo().search(domain_ci)
            # Get Chech Out
            domain_co = domain + [('check_out', '>=', date_check_in), ('check_out', '<=', date_check_out)]
            attendance_co = self.env['hr.attendance'].sudo().search(domain_co)
            # ==================================================================
            merged_set = set(attendance_ci).union(set(attendance_co))
            # Mengonversi kembali set ke daftar
            attendance_ids = list(merged_set)
            time = 'N/A'
            time_diff = False
            print(">>>>>>>>Nama:", employee_id.nama_lengkap)
            is_working = employee_id._is_work(time_today)
            print(">>>>>>>>Working:", is_working)
            if is_working:
                if len(attendance_ids) > 0:
                    for attendance in attendance_ids:
                        time = remove_seconds(attendance.check_in, attendance.type_ci)
                        if employee_id.id == attendance.mncei_employee_id.id:
                            if attendance.type_ci in ['Alpha', 'Late']:
                                if attendance.resouce_line_id or attendance.resouce_id:
                                    ci_time_act = (attendance.check_in + timedelta(hours=7))
                                    if attendance.resouce_line_id:
                                        work_ci = attendance.resouce_line_id.hour_from
                                    else:
                                        if attendance.resouce_id.attendance_ids:
                                            work_ci = attendance.resouce_id.attendance_ids[0].hour_from
                                    hours = int(work_ci + attendance.resouce_id.limit_attendance)
                                    minutes = int(((work_ci + attendance.resouce_id.limit_attendance) - hours) * 60)
                                    ci_time_plan = ci_time_act.replace(hour=hours, minute=minutes)
                                    time_diff = ci_time_act - ci_time_plan
                                res_data.append({
                                    'NIK': employee_id.nip_char,
                                    'name': employee_id.nama_lengkap,
                                    'time': time,
                                    'time_diff': time_diff,
                                })
                else:
                    res_data.append({
                        'NIK': employee_id.nip_char,
                        'name': employee_id.nama_lengkap,
                        'time': time,
                        'time_diff': time_diff,
                    })
        print("=======================")
        print(res_data)
        data = sorted(res_data, key=lambda x: x['time_diff'] if isinstance(x['time_diff'], timedelta) else timedelta.min, reverse=True)
        return data

    def create_logging(self, user_id, status, response):
        logging_obj = self.env['qontak.logging']
        logging_obj.create({
            'recipient': user_id.login,
            'code': status,
            'message': response,
        })
        return
