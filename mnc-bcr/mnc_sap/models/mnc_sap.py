from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

import firebase_admin
from firebase_admin import credentials, messaging, db

from odoo.http import request

import requests
import json
import string
import random
# =============================
# Change rules token
from google.oauth2 import service_account
import google.auth.transport.requests
# =============================


# =============== Notification ===============
def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def cek_url(url):
    # untuk local
    path_local = "C:/workspace/mnc_bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
    # untuk dev
    path_dev = "/home/devbcr/custom/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
    # untuk prod
    path_prod = "/opt/odoo14/custom-addons/mnc-bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
    # 192
    path_energy = "/home/custom/mnc-bcr/bcr_api_sh/static/js/motionminers-4b184-firebase-adminsdk-63njy-be5559e1e6.json"
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
    elif cek_my_host.find("202.147.195.19:8014") > 0:
        path_run = path_energy
        print("ini path server Energy")
    elif cek_my_host.find("devminers.mncenergy.com") > 0:
        path_run = path_energy
        print("ini path server Exabytes")
    else:
        path_run = path_local
        print("ini apa?")

    return path_run

# Get Path Json File
def firebase_json(url):
    # untuk local
    path_local = "C:/workspace/mnc_bcr/bcr_api_sh/static/js/firebase_master.json"
    # untuk prod
    path_prod = "/opt/odoo14/custom-addons/mnc-bcr/bcr_api_sh/static/js/firebase_master.json"
    # 192
    path_energy = "/home/custom/mnc-bcr/bcr_api_sh/static/js/firebase_master.json"
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
    elif cek_my_host.find("devminers.mncenergy.com") > 0:
        path_run = path_energy
        print("ini path server Energy")
    else:
        path_run = path_local
        print("ini apa?")

    return path_run


# Get Token Firebase
def get_scoopes():
    scoopes_url = request.env['ir.config_parameter'].sudo().get_param('scoopes_url')
    return scoopes_url


def get_token_firebase(path):
    credentials = service_account.Credentials.from_service_account_file(
      path, scopes=[get_scoopes()])
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token


def push_notification(title_value, message_par, mobile_token, login, code=False, res_id=False):
    # Cek url untuk file json
    if not firebase_admin._apps:
        cred = credentials.Certificate(
            cek_url(request.httprequest.host_url))
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://motionminers-4b184-default-rtdb.firebaseio.com/'
        })
    message_value = message_par
    if mobile_token:
        # server_token = request.env['push.notification.setting'].sudo().search([("code", "=", "STF")])[0].value
        path_firebase = firebase_json(request.httprequest.host_url)
        server_token = get_token_firebase(path_firebase)
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
                'data': {
                    'res_id': str(res_id.id),
                    'action': (res_id.state).upper(),
                    'menu': (code).upper()
                }
            }
        }
        response = requests.post("https://fcm.googleapis.com/v1/projects/motionminers-4b184/messages:send", headers=headers, data=json.dumps(body))
        print("Response Code: ", response.status_code)
        ref = db.reference('motion-mainers/')
        if db.reference('motion-mainers/notification'):
            notif = ref.child('notification')
            notif.update(
                {
                    id_generator(): {
                        'title': title_value,
                        'message': message_value,
                        'login': login,
                        'mobile_token': mobile_token,
                    }
                }
            )
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

# =============== ############ ===============


class sapform(models.Model):
    _name = 'sapform'
    _description = 'Safety Accountibility Program Form'
    _rec_name = "sap_no"

    def get_sequence(self):
        sequence = self.env['ir.sequence'].next_by_code('hazard.code')
        return sequence

    sap_no = fields.Char(string='SAP No', size=25, store=True, default='/')
    seq_number = fields.Integer(string='Seq Number', store=True, compute='_get_number_seq')
    company_id = fields.Many2one('res.company', string='Bisnis Unit', store=True, required=True)
    incident_date_time = fields.Datetime(string='Incident Date/Time', store=True, required=True)
    #
    location_id = fields.Many2one('location.point', string='Location',  store=True, required=True)
    detail_location = fields.Text('Details Location', store=True)
    risk_id = fields.Many2one('risk.level', string='Level Risk',  store=True)
    categ_id = fields.Many2one('category.hazard', string='Category',  store=True, required=True)
    danger_categ_id = fields.Many2one('category.danger', string='Danger Category', store=True, required=True)
    activity_id = fields.Many2one('activity.hazard', string='Activity', store=True, required=True)
    description = fields.Text(string='Description', size=250, store=True)
    img_eviden = fields.Binary(string='Eviden', store=True, attachment=True)
    #
    user_id = fields.Many2one('res.users', string="Suspect", store=True)
    other = fields.Boolean('Other', store=True)
    user_text = fields.Char('Suspect', store=True)
    penalty_id = fields.Many2one('penalty.point', string="Penalty", store=True)
    control_id = fields.Many2one('risk.control', string="Risk Control", store=True)
    report_department_id = fields.Many2one('department.hse', string="Department Reporting", store=True)
    department_id = fields.Many2one('department.hse', string="Department", store=True)
    pic_id = fields.Many2one('department.pic', string="PIC", store=True, domain="[('department_id', '=', department_id), ('status', '=', 'aktif')]", compute='_get_pic')
    child_pic =  fields.Many2one('child.pic', string="Teams", store=True, domain="[('parent_id', '=', pic_id), ('status', '=', 'aktif')]")
    description_result = fields.Text(string='Description', size=250, store=True)
    img_eviden_result = fields.Binary(string='Eviden', store=True, attachment=True)
    sap_type = fields.Selection([
        ('KTA', 'Kondisi Tidak Aman'),
        ('TTA', 'Tindakan Tidak Aman'),
        ('KA', 'Kondisi Aman'),
        ('TA', 'Tindakan Aman'),
    ], string="SAP Category", store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting'),
        ('hanging', 'Hanging'),
        ('close', 'Close'),
        ('reject', 'Reject')
    ], store=True, string="State", default='draft')
    act_repair = fields.Boolean('Self Repair', store=True)
    dept_uid = fields.Many2one('res.users', string="User PIC", related='pic_id.pic_id', store=True)
    act_repair_uid = fields.Many2one('res.users', string="Actual User Repair", store=True)
    reject_uid = fields.Many2one('res.users', string="Reject User", store=True)
    pic_uids = fields.Many2many('res.users', 'sap_user_rel', 'user_id', 'sap_id', string="User PIC", store=True, related='pic_id.pic_ids')
    fix_date = fields.Date('Fixing Date', store=True)
    fixing_date = fields.Datetime('Fixing Datetime', store=True)
    active = fields.Boolean('Active', store=True, default=True)
    revisi_notes = fields.Text('Revise Note', store=True)
    # Flagging
    is_not_relevan = fields.Boolean('Not Relevan', default=True, store=True)
    is_delegeted = fields.Boolean('Delegeted', store=True)
    is_hse_receive  = fields.Boolean('HSE Revise', store=True)

    @api.depends('sap_no', 'state')
    def _get_number_seq(self):
        for sap in self:
            nomor = 0
            if sap.sap_no and sap.state != 'draft':
                sequence = sap.sap_no
                print("SSSSSSSSSSSSSSS")
                print(sequence)
                split_sequence = sequence.split('/')
                print(split_sequence)
                nomor = int(split_sequence[1])
            sap.seq_number = nomor

    @api.depends('department_id')
    def _get_pic(self):
        for sap in self:
            dept_pic_id = self.env['department.pic'].search([('department_id', '=', sap.department_id.id), ('status', '=', 'aktif'), ('company_id', '=', sap.company_id.id)], limit=1)
            if dept_pic_id:
                sap.pic_id = dept_pic_id
            else:
                sap.pic_id = False

    @api.onchange('categ_id', 'sap_type')
    def change_type_sap(self):
        if self.categ_id:
            self.sap_type = self.categ_id.code or 'KA'

    @api.constrains('incident_date_time')
    def check_date_lock_incident(self):
        for sap in self:
            today = fields.Date.today()
            date_lock = today - timedelta(days=2)
            if sap.incident_date_time.date() < date_lock:
                raise ValidationError(_("Date Lock, you must be input today or H-1"))

    @api.constrains('sap_no')
    def check_sap_number(self):
        for sap in self:
            sap_id = self.env['sapform'].search([('sap_no', '=', sap.sap_no), ('id', '!=', sap.id), ('state', '!=', 'draft')], limit=1)
            if sap_id:
                raise ValidationError(_("Number Already Exist, Please change number"))

    def action_archive(self):
        self.write({'active': False})

    def action_submit(self, code=False):
        self.write({
            'state': 'waiting',
            'sap_no': self.categ_id.code + '/' + self.get_sequence()
        })
        return

    def action_complete(self, code=False):
        self.write({
            'state': 'close',
            'act_repair_uid': self.env.user.id,
            'fix_date': fields.Date.today(),
            'fixing_date': fields.Datetime.now(),
        })
        return

    def send_to_department(self, department_pic_id, not_relevan=False):
        if department_pic_id:
            if not_relevan:
                # Notification for Created
                self.send_notification(self.create_uid, "HSE-03", self)
                # Send to user HSE
                for user in department_pic_id.pic_ids:
                    self.send_notification(user, "HSE-12", self)
                return True
            else:
                print("XXXXXXXXXXXXXXXXXXXX")
                print(self)
                print(department_pic_id)
                print(self.act_repair_uid)
                for user in self.pic_id.pic_ids:
                    self.send_notification(user, "HSE-02", self)
                return True
        else:
            return False

    def action_to_waiting(self, department_id):
        dept_pic_id = self.env['department.pic'].search([('department_id', '=', department_id), ('status', '=', 'aktif'), ('company_id', '=', self.company_id.id)], limit=1)
        if dept_pic_id:
            self.write({
                'state': 'waiting'
            })
            result = self.send_to_department(dept_pic_id)
        else:
            result = False
        return result

    def action_not_relevan(self):
        self.update({
            'state': 'hanging',
            'is_not_relevan': False
        })
        dept_pic_id = self.env['department.pic'].search([('department_id.name', 'like', 'HSE'), ('status', '=', 'aktif'), ('company_id', '=', self.company_id.id)], limit=1) or False
        if dept_pic_id:
            self.update({
                'department_id': dept_pic_id.department_id.id
            })
        else:
            self.update({
                'department_id': False
            })
        result = self.send_to_department(dept_pic_id, not_relevan=True)
        return result

    def not_relevan_report(self, parameter):
        self.update({
            'state': 'hanging',
            'revisi_notes': parameter['reason'],
            'is_not_relevan': False,
            'reject_uid': self.env.uid
        })
        # dibuat send ke hse
        dept_pic_id = self.env['department.pic'].search([('department_id.name', 'like', 'HSE'), ('status', '=', 'aktif'), ('company_id', '=', self.company_id.id)], limit=1) or False
        if dept_pic_id:
            self.update({
                'department_id': dept_pic_id.department_id.id
            })
        else:
            self.update({
                'department_id': False
            })
        result = self.send_to_department(dept_pic_id, not_relevan=True)
        return result

    def get_pic(self, department_id, parameter):
        dept_pic_id = self.env['department.pic'].search([('department_id.id', '=', parameter['department']), ('status', '=', 'aktif'), ('company_id', '=', parameter['company'])], limit=1)
        if not dept_pic_id:
            raise ValidationError(_("Please Input User PIC"))
        return dept_pic_id

    def to_create(self, code, parameter, date_time, set_draft):
        sap_id = False
        datas = self.preapre_datas(parameter, date_time)
        datas['act_repair'] = parameter['self_repair']
        if code in ('KTA', 'TTA'):
            datas['risk_id'] = parameter['risk_level']
        # Create -> Save to Draft
        if set_draft:
            datas['state'] = 'draft'
            sap_id = self.create(datas)
        # Create -> Submit
        else:
            datas['sap_no'] = parameter['code'] + '/' + self.get_sequence()
            if parameter['self_repair'] and code not in ('KA', 'TA'):
                datas['state'] = 'close'
            elif code in ('KA', 'TA'):
                datas['state'] = 'close'
            else:
                datas['state'] = 'waiting'
            sap_id = self.create(datas)
            code_sap = "SAP"
            title_value = _("SAP No. %s") % (sap_id.sap_no)
            hse_dept_id = self.env['department.pic'].search([('department_id.name', 'like', 'HSE'), ('status', '=', 'aktif'), ('company_id', '=', sap_id.company_id.id)], limit=1) or False
            # Perbaikan Langsung
            if sap_id.act_repair:
                message = self.message_value(code='HSE-01', sap_id=sap_id)
                if hse_dept_id:
                    for user in hse_dept_id.pic_ids:
                        mobile_token = user.mobile_token
                        login = user.login
                        response = push_notification(title_value, message, mobile_token, login, code=code_sap, res_id=sap_id)
                        if response:
                            sap_id.create_push_notify(user, message, sap_id.state, sap_id.sap_type)
            # Report PIC
            if sap_id.state in ('waiting') and sap_id.pic_id:
                # Reporting
                message = self.message_value(code='HSE-02', sap_id=sap_id)
                for user in sap_id.pic_id.pic_ids:
                    mobile_token = user.mobile_token
                    login = user.login
                    response = push_notification(title_value, message, mobile_token, login, code=code_sap, res_id=sap_id)
                    if response:
                        sap_id.create_push_notify(user, message, sap_id.state, sap_id.sap_type)
            # KTA/KA
            if code in ('KA', 'TA'):
                if hse_dept_id:
                    for user_department in hse_dept_id.pic_ids:
                        user = user_department
                        sap_id.send_notification(user, "HSE-10", sap_id)
        return sap_id

    def preapre_datas(self, parameter, date_time):
        code = parameter['code']
        categ_id = self.env['category.hazard'].search([('code', '=', code)], limit=1)
        department_reporting = self.env['department.pic'].search(['|', ('child_ids.child_uid', '=', request.env.user.id), ('pic_ids', '=', request.env.user.id)], limit=1)

        datas = {
            "sap_no": '/',
            "sap_type": parameter['code'],
            "report_department_id": department_reporting.department_id.id or False,
            "company_id": parameter['company'],
            "incident_date_time": date_time,
            "location_id": parameter['location'],
            "detail_location": parameter['detail_location'] or "",
            "categ_id": categ_id.id,
            "danger_categ_id": parameter['category'],
            "activity_id": parameter['activity'],
            "description": parameter['incident_description'],
            "img_eviden": parameter['incident_photo'],
            "control_id": parameter['control_id']
        }
        if parameter['self_repair'] and code not in ('KA', 'TA'):
            datas['act_repair'] = True
            datas['act_repair_uid'] = request.env.user.id
            datas['fix_date'] = fields.Date.today()
            datas['fixing_date'] = fields.Datetime.now()
            datas['description_result'] = parameter['fixing_description']
            datas['img_eviden_result'] = parameter['fixing_photo']
        elif code in ('KA', 'TA'):
            datas['act_repair_uid'] = request.env.user.id
        else:
            datas['department_id'] = parameter['department'] or False
            pic_id = self.get_pic(parameter['department'], parameter)
            if pic_id:
                datas['pic_id'] = pic_id.id
        return datas

    def message_value(self, code, sap_id):
        hazard_notif = self.env['hazard.notification'].get_by_code(code)
        message = ''
        if hazard_notif:
            title = hazard_notif.notification_text
            if "[[risk_level]]" in title:
                if sap_id.risk_id:
                    title = title.replace("[[risk_level]]", sap_id.risk_id.risk_level)
                else:
                    title = title.replace("[[risk_level]]", "-")
            if "[[user_repair]]" in title:
                title = title.replace("[[user_repair]]", sap_id.act_repair_uid.name)
            if "[[user_report]]" in title:
                title = title.replace("[[user_report]]", sap_id.create_uid.name)
            if "[[department]]" in title:
                title = title.replace("[[department]]", sap_id.department_id.name)
            if "[[category]]" in title:
                title = title.replace("[[category]]", dict(sap_id._fields['sap_type'].selection).get(sap_id.sap_type))

            message = title
        return message

    def write(self, values):
        res = super(sapform, self).write(values)
        context = self.env.context
        if values.get('img_eviden_result'):
            self.add_attachment(self, values.get('img_eviden_result'), fixing=True)
        if values.get('img_eviden'):
            self.add_attachment(self, values.get('img_eviden'))
        if values.get('department_id'):
            department_id = self.env['department.hse'].browse(values.get('department_id'))
            if department_id.name != 'HSE':
                self.is_not_relevan = True
                self.is_hse_receive = False
            elif department_id.name == 'HSE':
                self.is_not_relevan = False
                self.is_hse_receive = True
            # Notification to PIC **Perubahan PIC pada Odoo
            if self.pic_id and self.state != 'close':
                for user in self.pic_id.pic_ids:
                    self.send_notification(user, "HSE-11", self)
        # Update in State Close
        if self.state == 'close' and context.get('form_view'):
            # to reporter
            report_uid = self.create_uid
            # self.send_update_data(report_uid)
            self.send_notification(report_uid, "HSE-09", self)
            # To PIC
            if self.pic_id:
                for user in self.pic_id.pic_ids:
                    self.send_notification(user, "HSE-09", self)
                    # self.send_update_data(user)
        return res

    # Method ketika saat di list view create split emails
    @api.model
    def create(self, vals):
        res = super(sapform, self).create(vals)
        if vals.get('img_eviden_result'):
            res.add_attachment(res, vals.get('img_eviden_result'), fixing=True)
        if vals.get('img_eviden'):
            res.add_attachment(res, vals.get('img_eviden'))
        return res

    def send_update_data(self, user_id):
        email_template = self.env.ref('mnc_sap.notification_update_close').with_context(dbname=self._cr.dbname, invited_users=user_id)
        email_template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user_id.login})
        return

    # Func Notification
    def send_notification(self, user, code_message, sap_id):
        title_value = _("SAP No. %s") % (sap_id.sap_no)
        code = "SAP"
        message_delegated = self.message_value(code=code_message, sap_id=sap_id)
        mobile_token = user.mobile_token
        login = user.login
        response = push_notification(title_value, message_delegated, mobile_token, login, code=code, res_id=sap_id)
        if response:
            sap_id.create_push_notify(user, message_delegated, sap_id.state, sap_id.sap_type)
        return

    def create_push_notify(self, user_id, message, action, code):
        push_id = self.env["push.notification"].create({
            "user": user_id.id,
            "topic": "notification",
            "title": "notification person",
            'code': code,
            'action': action,
            "message": message,
            "res_id": self.id,
        })
        print(push_id)
        return push_id

    # -------- To Create Attachment ------
    def add_attachment(self, sap_id, filename=False, fixing=False):
        domain = [('res_id', '=', sap_id.id), ('res_model', '=', 'sapform'), ('company_id', '=', sap_id.company_id.id)]
        if fixing:
            domain += [('res_field', '=', 'img_eviden_result')]
        else:
            domain += [('res_field', '=', 'img_eviden')]

        attachment = self.env['ir.attachment'].create(
            {
                'name': sap_id.sap_no,
                'company_id': sap_id.company_id.id,
                'public': True,
                'type': 'binary',
                'datas': filename,
                'res_model': 'sapform',
                'res_id': sap_id.id
            })
        if fixing:
            attachment.write({
                'res_field': 'img_eviden_result'
            })
        else:
            attachment.write({
                'res_field': 'img_eviden'
            })
        return attachment
