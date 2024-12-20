import firebase_admin
import requests
import json
import logging
import string
import random

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, format_date
from collections import defaultdict
from datetime import datetime, timedelta
from firebase_admin import credentials, messaging, db
# =============================
# Change rules token
from google.oauth2 import service_account
import google.auth.transport.requests
# =============================

from ..controllers.leave_request import MncLeave

from odoo.http import request

_logger = logging.getLogger(__name__)


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
    elif cek_my_host.find("devminers.mncenergy.com") > 0:
        path_run = path_energy
        print("ini path server Exabytes")
    else:
        path_run = path_local
        print("ini apa?")
    return path_run


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


def get_scoopes():
    scoopes_url = request.env['ir.config_parameter'].sudo().get_param('scoopes_url')
    return scoopes_url


def get_token_firebase(path):
    credentials = service_account.Credentials.from_service_account_file(
      path, scopes=[get_scoopes()])
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token


def push_notification(title_value, message_par, mobile_token, login, res_id=False):
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
                "data": {
                    'res_id': str(res_id.leave_id.id),
                    'action': ('approval').upper(),
                    'menu': 'LEAVE'
                }
            }
        }
        response = requests.post("https://fcm.googleapis.com/v1/projects/motionminers-4b184/messages:send", headers=headers, data=json.dumps(body))
        print('Body: ', body)
        print('Response Code: ', response)
        print('Response Text: ', response.json())
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
            notif.set(
                {
                    id_generator(): {
                        'title': title_value,
                        'message': message_value,
                        'login': login,
                        'mobile_token': mobile_token,
                    }
                }
            )
        result = {
            "code": 2,
            "desc": 'Success'}
        return result
    else:
        result = {
            "code": 3,
            "desc": 'failed'}
        return result


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    type_leave = fields.Selection([
        ('normal', 'Normal'),
        ('change_leave', 'Change Leave'),
        ('sick_leave', 'Sick Leave'),
        ('special_leave', 'Special Off'),
        ('roster', 'Roster'),
        ('roster_other', 'Roster & Other'),
    ], store=True, string="Type Leaves", tracking=True)
    mnc_allocation_type = fields.Selection([
        ('no', 'No Limit'),
        ('fixed', 'Set by Time Off Officer')],
        default='no', string='Mode',
        help='\tNo Limit: no allocation by default, users can freely request time off; '
             '\tAllow Employees Requests: allocated by HR and users can request time off and allocations; '
             '\tSet by Time Off Officer: allocated by HR and cannot be bypassed; users can request time off;')
    allocation_validation_type = fields.Selection([
        ('hr', 'By Time Off Officer'),
        ('manager', "By Employee's Manager"),
        ('both', "By Employee's Manager and Time Off Officer")], default='hr', string='Allocation Validation')
    with_detail = fields.Boolean("With Details", store=True)
    type_details_ids = fields.One2many('hr.leave.type.details', 'leave_type_id', string='Details')
    company_id = fields.Many2one('res.company', string='Company', default=False)
    responsible_id = fields.Many2one('res.users', string='Responsible', default=False, required=False)
    submission_type = fields.Selection([
        ('none', 'None'),
        ('<', "<")
    ], default='none', string='Submission Leave', store=True,
    help='\tNone : tidak ada batasan kapan harus mengajukan tanggal cuti '
         '\n< : Minimum hari kapan cuti bisa diajukan')
    duration_days = fields.Integer('Duration Days', default=14, store=True)
    max_request = fields.Integer("Max Request in Days", default=0, store=True)
    user_responsible_ids = fields.Many2many(
        'res.users', 'leave_type_response_rel', 'leave_type_id', 'responsible_id',
        string='Responsible', store=True, copy=False
    )

    @api.onchange('mnc_allocation_type')
    def change_allocation_type(self):
        if self.mnc_allocation_type:
            self.allocation_type = self.mnc_allocation_type

    # ============================ Override ============================
    def _search_max_leaves(self, operator, value):
        value = float(value)
        employee_id = self._get_contextual_employee_id()
        leaves = defaultdict(int)

        if employee_id:
            allocations = self.env['hr.leave.allocation'].search([
                ('mncei_employee_id', '=', employee_id),
                ('state', '=', 'validate')
            ])
            for allocation in allocations:
                leaves[allocation.holiday_status_id.id] += allocation.number_of_days

        valid_leave = []
        for leave in leaves:
            if operator == '>':
                if leaves[leave] > value:
                    valid_leave.append(leave)
            elif operator == '<':
                if leaves[leave] < value:
                    valid_leave.append(leave)
            elif operator == '=':
                if leaves[leave] == value:
                    valid_leave.append(leave)
            elif operator == '!=':
                if leaves[leave] != value:
                    valid_leave.append(leave)

        return [('id', 'in', valid_leave)]

    @api.depends_context('mncei_employee_id', 'default_mncei_employee_id', 'last_yearly')
    def _compute_leaves(self):
        data_days = {}
        employee_id = self._get_contextual_employee_id()
        is_last_year = self._get_contextual_last_yearly()

        if employee_id:
            data_days = self.get_employees_days([employee_id], is_last_year)[employee_id]

        for holiday_status in self:
            result = data_days.get(holiday_status.id, {})
            holiday_status.max_leaves = result.get('max_leaves', 0)
            holiday_status.leaves_taken = result.get('leaves_taken', 0)
            holiday_status.remaining_leaves = result.get('remaining_leaves', 0)
            holiday_status.virtual_remaining_leaves = result.get('virtual_remaining_leaves', 0)
            holiday_status.virtual_leaves_taken = result.get('virtual_leaves_taken', 0)

    def get_employees_days(self, employee_ids, last_yearly=False):
        result = {
            employee_id: {
                leave_type.id: {
                    'max_leaves': 0,
                    'leaves_taken': 0,
                    'remaining_leaves': 0,
                    'virtual_remaining_leaves': 0,
                    'virtual_leaves_taken': 0,
                } for leave_type in self
            } for employee_id in employee_ids
        }
        in_yearly = (fields.Datetime.now().year)

        requests = self.env['hr.leave'].search([
            ('mncei_employee_id', 'in', employee_ids),
            ('state', 'in', ['validate']),
            ('holiday_status_id', 'in', self.ids)
        ])
        # Request
        if last_yearly:
            last_yearly = (in_yearly - 1)
            start = '%s-01-01 00:00:00' % (last_yearly)
            end = '%s-12-31 23:59:00' % (last_yearly)
            requests = self.env['hr.leave'].search([
                ('mncei_employee_id', 'in', employee_ids),
                ('date_from', '>=', start),
                ('date_to', '<=', end),
                ('state', 'in', ['validate']),
                ('holiday_status_id', 'in', self.ids)
            ])
        else:
            # yearly = (fields.Datetime.now().year)
            start = '%s-01-01 00:00:00' % (in_yearly)
            end = '%s-12-31 23:59:00' % (in_yearly)
            requests = self.env['hr.leave'].search([
                ('mncei_employee_id', 'in', employee_ids),
                ('date_from', '>=', start),
                ('date_to', '<=', end),
                ('state', 'in', ['validate']),
                ('holiday_status_id', 'in', self.ids)
            ])
        # Allocation
        if last_yearly:
            last_yearly = (in_yearly - 1)
            start = '%s-01-01 00:00:00' % (last_yearly)
            end = '%s-12-31 23:59:00' % (last_yearly)
            allocations = self.env['hr.leave.allocation'].search([
                ('mncei_employee_id', 'in', employee_ids),
                ('period_start', '>=', start),
                ('period_end', '<=', end),
                ('state', 'in', ['confirm', 'validate1', 'validate']),
                ('holiday_status_id', 'in', self.ids)
            ])
        else:
            # yearly = (fields.Datetime.now().year)
            start = '%s-01-01 00:00:00' % (in_yearly)
            end = '%s-12-31 23:59:00' % (in_yearly)
            allocations = self.env['hr.leave.allocation'].search([
                ('mncei_employee_id', 'in', employee_ids),
                ('period_start', '>=', start),
                ('period_end', '<=', end),
                ('state', 'in', ['confirm', 'validate1', 'validate']),
                ('holiday_status_id', 'in', self.ids)
            ])

        for request in requests:
            status_dict = result[request.mncei_employee_id.id][request.holiday_status_id.id]
            status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
                                                    if request.leave_type_request_unit == 'hour'
                                                    else request.number_of_days)
            status_dict['virtual_leaves_taken'] += (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)
            if request.state == 'validate':
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                            if request.leave_type_request_unit == 'hour'
                                            else request.number_of_days)
                status_dict['remaining_leaves'] -= (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)

        for allocation in allocations.sudo():
            status_dict = result[allocation.mncei_employee_id.id][allocation.holiday_status_id.id]
            if allocation.state == 'validate':
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible
                status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                          if allocation.type_request_unit == 'hour'
                                                          else allocation.number_of_days)
                status_dict['max_leaves'] += (allocation.number_of_hours_display
                                            if allocation.type_request_unit == 'hour'
                                            else allocation.number_of_days)
                status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                  if allocation.type_request_unit == 'hour'
                                                  else allocation.number_of_days)
        return result

    def _get_contextual_last_yearly(self):
        is_last_year = False
        if 'last_yearly' in self._context:
            is_last_year = self._context['last_yearly']
        return is_last_year

    def _get_contextual_employee_id(self):
        if 'employee_id' in self._context:
            employee_id = self._context['employee_id']
        elif 'mncei_employee_id' in self._context:
            employee_id = self._context['mncei_employee_id']
        elif 'default_employee_id' in self._context:
            employee_id = self._context['default_employee_id']
        else:
            employee_id = self.env.user.mncei_employee_id.id
        return employee_id
    # ======== ///////////////////////////////////////////// ===========


class LeaveTypeDetails(models.Model):
    _name = 'hr.leave.type.details'

    name = fields.Char("Name", store=True)
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Types", store=True, ondelete='cascade')
    type_leave = fields.Selection([
        ('normal', 'Normal'),
        ('change_leave', 'Change Leave'),
        ('sick_leave', 'Sick Leave'),
        ('special_leave', 'Special Off'),
        ('roster', 'Roster'),
        ('roster_other', 'Roster & Other'),
    ], store=True, string="Type Leaves", related='leave_type_id.type_leave', tracking=True)
    quota_leave = fields.Integer('Quota', store=True)
    submission_type = fields.Selection([
        ('none', 'None'),
        ('<', "<"),
    ], default='none', string='Submission Leave', store=True,
    help='\tNone : tidak ada batasan kapan harus mengajukan tanggal cuti '
         '\n< : Minimum hari kapan cuti bisa diajukan')
    can_edit = fields.Boolean('Can Edit', store=True)
    duration_days = fields.Integer('Duration Days', default=14, store=True)


class HRLeave(models.Model):
    _inherit = "hr.leave"

    request_date = fields.Datetime('Request Date', store=True)
    carteker_id = fields.Many2one(
        'res.users', store=True, string='Caretaker')
    employee_cartaker_id = fields.Many2one('mncei.employee', related='carteker_id.mncei_employee_id', string="Employee", default=False, ondelete='cascade', index=True, store=True)
    user_id = fields.Many2one('res.users', string='User', related=False, related_sudo=True, compute_sudo=True, store=True, default=lambda self: self.env.uid, readonly=True)
    mncei_employee_id = fields.Many2one('mncei.employee', related='user_id.mncei_employee_id', string="Employee", default=False, ondelete='cascade', index=True, store=True)
    can_edit = fields.Boolean('Can Edit', compute='_get_can_edit', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancel Request'),  # YTI This state seems to be unused. To remove
        ('confirm', 'Waiting Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved'),
        ('reject', 'Decline')
        ], string='Status', default='draft', compute='_compute_state', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Submit', when a time off request is created." +
        "\nThe status is 'To Approve', when time off request is confirmed by user." +
        "\nThe status is 'Refused', when time off request is refused by manager." +
        "\nThe status is 'Approved', when time off request is approved by manager.")
    holiday_detail_id = fields.Many2one('hr.leave.type.details', string='Details', store=True)
    type_leave = fields.Selection([
        ('normal', 'Normal'),
        ('change_leave', 'Change Leave'),
        ('sick_leave', 'Sick Leave'),
        ('special_leave', 'Special Off'),
        ('roster', 'Roster'),
        ('roster_other', 'Roster & Other'),
    ], string="Type Leaves", related='holiday_status_id.type_leave', tracking=True)
    replace_date_from = fields.Date('Replace Date From', store=True)
    replace_date_to = fields.Date('Replace Date To', store=True)
    roster_date_from = fields.Date('Roster Date From', store=True)
    roster_date_to = fields.Date('Roster Date To', store=True)
    is_replace = fields.Boolean("Replace", compute='_get_is_replace')
    is_roster = fields.Boolean("Roster", compute='_get_is_roster')
    is_sick_leave = fields.Boolean("Sick Leave", compute='_get_is_sick')
    active = fields.Boolean('Active', store=True, default=True)

    # Approval
    approval_ids = fields.One2many('hr.leave.approval', 'leave_id', compute='add_approval', string="Approval List", store=True, ondelete='cascade', copy=False)
    approve_uid = fields.Many2one(
        'res.users',
        string='User Approve', store=True, readonly=True, copy=False
    )
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_leave_user_rel', 'leave_id', 'user_id',
        string='Approvals', store=True, copy=False
    )
    approval_id = fields.Many2one(
        'hr.leave.approval',
        string='Approval', store=True, readonly=True
    )
    attachment = fields.Binary(string='Attachment', store=True, attachment=True)
    filename_attachment = fields.Char(string='Filename', store=True)

    _sql_constraints = [
        ('duration_check', "CHECK ( number_of_days >= 0 )", "The number of days must be greater than 0."),
        ('number_per_interval_check', "CHECK(number_per_interval > 0)", "The number per interval should be greater than 0"),
        ('interval_number_check', "CHECK(interval_number > 0)", "The interval number should be greater than 0"),
    ]

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date_state(self):
        if self.env.context.get('leave_skip_state_check'):
            return
        for holiday in self:
            if holiday.state in ['cancel', 'refuse']:
                raise ValidationError(_("This modification is not allowed in the current state."))

    @api.depends('holiday_detail_id')
    def _get_can_edit(self):
        for leave in self:
            if leave.holiday_detail_id:
                leave.can_edit = leave.holiday_detail_id.can_edit
            else:
                leave.can_edit = False

    @api.depends('holiday_status_id', 'type_leave')
    def _get_is_sick(self):
        for leave in self:
            if leave.holiday_status_id.type_leave == 'sick_leave':
                leave.is_sick_leave = True
            else:
                leave.is_sick_leave = False

    @api.depends('holiday_status_id', 'type_leave')
    def _get_is_roster(self):
        for leave in self:
            if leave.holiday_status_id.type_leave == 'roster' or leave.holiday_status_id.type_leave == 'roster_other':
                leave.is_roster = True
            else:
                leave.is_roster = False

    @api.depends('holiday_status_id', 'type_leave')
    def _get_is_replace(self):
        for leave in self:
            if leave.holiday_status_id.type_leave == 'change_leave':
                leave.is_replace = True
            else:
                leave.is_replace = False

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return

        current_employee = self.env.user.mncei_employee_id
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')

        for holiday in self:
            val_type = holiday.validation_type

            if not is_manager and state != 'confirm':
                if state == 'draft':
                    # if holiday.state == 'refuse':
                    #     raise UserError(_('Only a Time Off Manager can reset a refused leave.'))
                    # if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
                    #     raise UserError(_('Please request date must be greater than today.'))
                    if holiday.mncei_employee_id != current_employee:
                        raise UserError(_('Only a Time Off Manager can reset other people leaves.'))
                else:
                    if val_type == 'no_validation' and current_employee == holiday.mncei_employee_id:
                        continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    holiday.check_access_rule('write')

                    # This handles states validate1 validate and refuse
                    # if holiday.mncei_employee_id != current_employee:
                    #     raise UserError(_('Only a Time Off Manager can approve/refuse its own requests.'))

                    # ================= Override ===============
                    # if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and holiday.holiday_type == 'employee':
                    #     if not is_officer and self.env.user != holiday.employee_id.leave_manager_id:
                    #         raise UserError(_('You must be either %s\'s manager or Time off Manager to approve this leave') % (holiday.mncei_employee_id.nama_lengkap))

                    # if not is_officer and (state == 'validate' and val_type == 'hr') and holiday.holiday_type == 'employee':
                    #     raise UserError(_('You must either be a Time off Officer or Time off Manager to approve this leave'))
                    # ================= Override ===============

    def get_users(self, employee_id):
        user_id = self.env['res.users'].search([('mncei_employee_id', '=', employee_id.id)])
        return user_id

    @api.depends('carteker_id', 'mncei_employee_id')
    def add_approval(self):
        for leave in self:
            approval_obj = self.env['hr.leave.approval']
            if leave.mncei_employee_id:
                approval_list = []
                # Get User
                users = [leave.carteker_id]
                if leave.holiday_status_id.type_leave not in ['sick_leave']:
                    print("==========Users A=============")
                    # Aturan approval cuti adalah, memiliki 4 approval
                    # 1. Cartaker
                    # 2. Atasan Langsung (Condition)
                    # 3. Department Head
                    # 3. Director 1
                    head_users = False
                    if leave.mncei_employee_id.head_user1:
                        head_users = leave.get_users(leave.mncei_employee_id.head_user1)
                        if not head_users:
                            raise ValidationError(_("Please set employee user relation Direct Employee"))
                        else:
                            users.append(head_users)
                    # Check Department Head
                    if leave.mncei_employee_id.head_user2:
                        department_head = leave.get_users(leave.mncei_employee_id.head_user2)
                        if leave.user_id != department_head:
                            users.append(department_head)
                    else:
                        raise ValidationError(_("Please set employee user relation Dept Head"))
                    # Check Director 1
                    if leave.mncei_employee_id.director_1:
                        director_1 = leave.get_users(leave.mncei_employee_id.director_1)
                        users.append(director_1)
                    else:
                        raise ValidationError(_("Please set employee user relation Director"))
                else:
                    head_users = False
                    # Direct Employee
                    if leave.mncei_employee_id.head_user1:
                        head_users = leave.get_users(leave.mncei_employee_id.head_user1)
                    # Jika tidak memiliki Direct Employee maka mengambil Department Head
                    elif leave.mncei_employee_id.head_user2 and not leave.mncei_employee_id.head_user1:
                        head_users = leave.get_users(leave.mncei_employee_id.head_user2)
                        # if head_users 

                    if not head_users:
                        raise ValidationError(_("Please set employee user relation Dept Head"))
                    else:
                        if leave.user_id != head_users:
                            users.append(head_users)
                number = 1
                total_datas = len(users)
                for user_id in users:
                    app_id = approval_obj.create(leave.prepare_data_approval(user_id, number, total_datas))
                    approval_list.append(app_id.id)
                    number += 1
                    # Set Value
                leave.approval_ids = [(6, 0, approval_list)]

    def prepare_data_approval(self, user_id, number, total_datas):
        data = {
            'user_id': user_id.id,
            'email': user_id.login,
            'leave_id': self.id
        }
        if total_datas == 3:
            if number == 1:
                data['jabatan'] = "Caretaker"
            if number == 2:
                data['jabatan'] = "Department Head"
            if number == 3:
                data['jabatan'] = "Director"
        else:
            if number == 1:
                data['jabatan'] = "Caretaker"
            if number == 2:
                data['jabatan'] = "Direct Employee"
            if number == 3:
                data['jabatan'] = "Department Head"
            if number == 4:
                data['jabatan'] = "Director"
        return data

    def _search_leave(self, start_date, end_date):
        leave_ids = []
        start = start_date.date()
        end = end_date.date()
        datas_1 = self.env['hr.leave'].search([('state', 'in', ['confirm', 'validate']), ('request_date_from', '>=', start), ('request_date_from', '<=', end), ('user_id', '=', self.env.uid)])
        datas_2 = self.env['hr.leave'].search([('state', 'in', ['confirm', 'validate']), ('request_date_to', '>=', start), ('request_date_to', '<=', end), ('user_id', '=', self.env.uid)])
        leave_ids = set(datas_1).union(set(datas_2))
        print("Leaves: ", leave_ids)
        if leave_ids:
            raise ValidationError(_("leave request have exist"))

    def check_mass_leave(self):
        get_year = (fields.Datetime.now().year)
        start = '%s-01-01' % (get_year)
        end = '%s-12-31' % (get_year)
        mass_leave_domain = [('date_start', '>=', start), ('date_end', '<=', end), ('state', '=', 'verified')]
        mass_leave_ids = self.env['hr.holidays.public'].sudo().search(mass_leave_domain)
        total_days = 0
        for mass_leave_id in mass_leave_ids:
            for line in mass_leave_id.line_ids.filtered(lambda x: x.date >= self.request_date_from and x.date <= self.request_date_to):
                total_days += 1
        return total_days

    def _check_quota_leave(self):
        mass_leave_days = 0
        if not self.mncei_employee_id.roster_id:
            mass_leave_days = self.check_mass_leave()
        if self.holiday_status_id.type_leave == 'roster':
            calc_duration = self.calculate_days_per_month(self.request_date_from, self.request_date_to)
            period_site = self.calculate_days_per_month(self.roster_date_from, self.roster_date_to)
            total_in_days = sum(calc_duration.values()) - mass_leave_days
            roster_id = self.mncei_employee_id.roster_id
            if roster_id:
                total_in_days_site = sum(period_site.values())
                if roster_id.total_workdays > total_in_days_site:
                    raise ValidationError(_("Total Period Site anda kurang dari ketentuan."))
                if roster_id.total_off != total_in_days:
                    raise ValidationError(_("Total Request anda melebihi ketentuan."))
            else:
                raise ValidationError(_("Anda tidak mendapatkan roster."))
        if self.holiday_status_id.type_leave == 'special_leave':
            calc_duration = self.calculate_days_per_month(self.request_date_from, self.request_date_to)
            total_in_days = sum(calc_duration.values()) - mass_leave_days
            if self.holiday_detail_id.quota_leave < total_in_days:
                raise ValidationError(_("Total Request anda melebihi ketentuan."))
            else:
                return True
        if self.holiday_status_id.type_leave == 'normal':
            # Get Natioanal Off & Cuber in Year
            get_year = (fields.Datetime.now().year)
            start = '%s-01-01' % (get_year)
            end = '%s-12-31' % (get_year)
            domain = [('date_start', '>=', start), ('date_end', '<=', end), ('state', '=', 'verified')]
            mass_leave_id = request.env['hr.holidays.public'].sudo().search(domain, limit=1)
            # =========================================
            # Cuti Bersama Last Year
            get_year = (fields.Datetime.now().year - 1)
            last_start = '%s-01-01' % (get_year)
            last_end = '%s-12-31' % (get_year)
            last_year_domain = [('date_start', '>=', last_start), ('date_end', '<=', last_end), ('state', '=', 'verified')]
            last_mass_leave_id = request.env['hr.holidays.public'].sudo().search(last_year_domain, limit=1)
            if last_mass_leave_id:
                total_mass_leave_last_year = last_mass_leave_id.total_days
            else:
                total_mass_leave_last_year = 0
            # =========================================
            leave_type = self.holiday_status_id.with_context(mncei_employee_id=self.mncei_employee_id.id)
            last_leave_type = self.holiday_status_id.with_context(mncei_employee_id=self.mncei_employee_id.id, last_yearly=True)

            # Kalkulasi dalam cuti
            calc_duration = self.calculate_days_per_month(self.request_date_from, self.request_date_to)
            list_values = [calc_duration[i] for i in calc_duration.keys()]

            # Carry Over
            carry_over = (last_leave_type.remaining_leaves - total_mass_leave_last_year)
            # Get My Balance
            my_timeoff = MncLeave.getDataLeaveDetails(self)['data']
            remain_in_year = (leave_type.remaining_leaves - mass_leave_id.total_days)
            balance = my_timeoff['balance']
            if len(calc_duration) > 1:
                secound_value = list_values[1]
                first_month = next(iter(calc_duration))
                if first_month <= 3:
                    duration_carry_over = calc_duration[first_month]
                    if carry_over > 0:
                        actual_result_last_year = carry_over - duration_carry_over
                        if actual_result_last_year < 0:
                            carry_over = max((actual_result_last_year), 0.0)
                            balance -= abs(actual_result_last_year) + secound_value
                        else:
                            balance -= secound_value
                            carry_over = actual_result_last_year
                else:
                    request_total = sum(list_values) - mass_leave_days
                    remain_in_year -= request_total
            else:
                month = list(calc_duration.keys())
                if month[0] <= 3:
                    duration_carry_over = calc_duration[month[0]]
                    if carry_over > 0:
                        actual_result_last_year = carry_over - duration_carry_over
                        if actual_result_last_year < 0:
                            carry_over = max((actual_result_last_year), 0.0)
                            balance -= abs(actual_result_last_year)
                        else:
                            carry_over = actual_result_last_year
                else:
                    request_total = sum(list_values) - mass_leave_days
                    balance -= request_total

            print("========Result=========")
            print("Remaining In Year :", balance)
            print("Remaining Last Year :", carry_over)
            if remain_in_year < 0:
                raise ValidationError(_("leave request melebihi quota cuti anda"))
            return True

    def calculate_days_per_month(self, start_date, end_date):
        """
        Menghitung jumlah hari di setiap bulan antara dua tanggal yang diberikan.

        Parameters:
        start_date (str): Tanggal mulai dalam format 'YYYY-MM-DD'
        end_date (str): Tanggal akhir dalam format 'YYYY-MM-DD'

        Returns:
        dict: Jumlah hari di setiap bulan antara dua tanggal
        """
        start = start_date
        end = end_date

        if start > end:
            return "Tanggal mulai harus sebelum tanggal akhir"

        days_per_month = defaultdict(int)
        current = start

        while current <= end:
            month_start = current.replace(day=1)
            next_month = month_start + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(days=1)

            if month_end > end:
                month_end = end
            # Cek working time Site and HO(1)
            if not self.mncei_employee_id.roster_id:
                days_in_current_month = self._get_number_of_days(datetime.combine(current, datetime.min.time()), datetime.combine(month_end, datetime.max.time()), 1)['days']
            else:
                days_in_current_month = self._get_number_of_days(datetime.combine(current, datetime.min.time()), datetime.combine(month_end, datetime.max.time()), 2)['days']

            days_per_month[current.month] += days_in_current_month

            current = month_end + timedelta(days=1)

        return dict(days_per_month)

    def action_submit(self):
        for leave in self:
            if leave.holiday_status_id.type_leave in ['normal', 'special_leave', 'roster'] and leave.holiday_status_id.mnc_allocation_type == 'fixed':
                leave._check_quota_leave()
            approval_id = leave.approval_ids.sorted(lambda x: x.id)[0]
            approval_id.write({'is_current_user': True})
            leave.write({
                'request_date': fields.Date.today(),
                'state': 'confirm',
                'approve_uid': leave.approval_ids[0].user_id.id,
                'approval_id': approval_id.id
            })
            approval_id.write({
                'is_email_sent': True,
                'is_current_user': True,
            })
        return

    # Override
    @api.depends('holiday_status_id')
    def _compute_state(self):
        for holiday in self:
            holiday.state = 'draft'

    # Override
    @api.depends('holiday_type')
    def _compute_from_holiday_type(self):
        for holiday in self:
            if holiday.holiday_type == 'employee':
                if not holiday.employee_id:
                    holiday.employee_id = self.env.user.employee_id
                holiday.mode_company_id = False
                holiday.category_id = False
            elif holiday.holiday_type == 'company':
                holiday.employee_id = False
                if not holiday.mode_company_id:
                    holiday.mode_company_id = self.env.company.id
                holiday.category_id = False
            elif holiday.holiday_type == 'department':
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.category_id = False
            elif holiday.holiday_type == 'category':
                holiday.employee_id = False
                holiday.mode_company_id = False
            else:
                holiday.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id
                holiday.mncei_employee_id = self.env.user.mncei_employee_id

    def _check_date_request(self, holiday_status_id, create_date, request_date_from, holiday_detail_id=False,):
        duration_request = request_date_from - create_date
        if holiday_status_id.type_leave != 'special_leave':
            if holiday_status_id.submission_type != 'none':
                if duration_request.days < holiday_status_id.duration_days or duration_request.days <= 0:
                    raise ValidationError(_("Request date must be > %s days") % (str(holiday_status_id.duration_days)))
        else:
            if holiday_detail_id:
                detail_leave_id = self.env['hr.leave.type.details'].browse(holiday_detail_id)
                if detail_leave_id.submission_type != 'none':
                    if duration_request.days < detail_leave_id.duration_days or duration_request.days <= 0:
                        raise ValidationError(_("Request date must be > %s days") % (str(detail_leave_id.duration_days)))
            else:
                raise ValidationError(_("Please input detail leave"))

    def to_create(self, parameter, carteker_id, code=False):
        date_format = "%Y-%m-%d"
        if not parameter['date_from'] or not parameter['date_to']:
            raise ValidationError(_("Please input Date From/To"))
        # Check Leave Request Existing
        self._search_leave(datetime.combine(datetime.strptime(parameter['date_from'], date_format).date(), datetime.min.time()), datetime.combine(datetime.strptime(parameter['date_to'], date_format).date(), datetime.max.time()), )
        holiday_status_id = self.env['hr.leave.type'].browse(parameter['leave_id'])
        # ===================================================
        if parameter['leave_line_id']:
            self._check_date_request(holiday_status_id, fields.Datetime.now(), datetime.strptime(parameter['date_from'], date_format), holiday_detail_id=parameter['leave_line_id'])
        else:
            self._check_date_request(holiday_status_id, fields.Datetime.now(), datetime.strptime(parameter['date_from'], date_format))

        leave_id = self.create({
            "holiday_status_id": holiday_status_id.id,
            "request_date_from": datetime.strptime(parameter['date_from'], date_format).date(),
            "request_date_to": datetime.strptime(parameter['date_to'], date_format).date(),
            "date_from": datetime.combine(datetime.strptime(parameter['date_from'], date_format).date(), datetime.min.time()),
            "date_to": datetime.combine(datetime.strptime(parameter['date_to'], date_format).date(), datetime.max.time()),
            "name": parameter['reason'],
            "state": "draft",
            "carteker_id": carteker_id.id
        })
        if holiday_status_id.type_leave == 'sick_leave':
            if not parameter['attachment']:
                raise ValidationError(_("Please Input attachment"))
            else:
                leave_id.write({
                    'attachment': parameter['attachment'],
                })
                leave_id.add_attachment(leave_id, parameter['attachment'])
        # Check Roster
        if holiday_status_id.type_leave == 'roster':
            if not parameter['roster_date_from'] or not parameter['roster_date_to']:
                raise ValidationError(_("Please Input Working Dates"))
        # Change Leave
        if holiday_status_id.type_leave == 'change_leave':
            if not parameter['replace_date_from'] or not parameter['replace_date_to']:
                raise ValidationError(_("Please Input Working Dates"))

        params = {}
        if parameter['leave_line_id']:
            params['holiday_detail_id'] = parameter['leave_line_id']
        # Roster
        if parameter['roster_date_from'] and parameter['roster_date_to']:
            params['roster_date_from'] = datetime.strptime(parameter['roster_date_from'], date_format).date()
            params['roster_date_to'] = datetime.strptime(parameter['roster_date_to'], date_format).date()
            params['is_roster'] = True
        # Replace Date
        if parameter['replace_date_from'] and parameter['replace_date_to']:
            params['replace_date_from'] = datetime.strptime(parameter['replace_date_from'], date_format).date()
            params['replace_date_to'] = datetime.strptime(parameter['replace_date_to'], date_format).date()
            params['is_replace'] = True
        # Duration Days
        # Kerja Tanpa Roster
        total_in_days = 1
        if not leave_id.mncei_employee_id.roster_id:
            mass_leave_days = leave_id.check_mass_leave()
            calc_duration = leave_id.calculate_days_per_month(leave_id.request_date_from, leave_id.request_date_to)
            total_in_days = (sum(calc_duration.values()) - mass_leave_days)
            params['number_of_days'] = total_in_days
        # Karyawan Roster
        else:
            calc_duration = leave_id.calculate_days_per_month(leave_id.request_date_from, leave_id.request_date_to)
            total_in_days = sum(calc_duration.values()) + 1
            params['number_of_days'] = total_in_days
        if holiday_status_id.max_request > 0:
            if holiday_status_id.max_request < total_in_days:
                raise ValidationError(_("Cuti anda melebihi ketentuan dalam satu kali pengajuan."))
        # Update Datas
        leave_id.write(params)
        if code != 'draft':
            leave_id.action_submit()
        elif code == 'draft':
            leave_id.write({'state': 'draft'})
        return leave_id

    @api.model_create_multi
    def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        if not self._context.get('leave_fast_create'):
            leave_types = self.env['hr.leave.type'].browse([values.get('holiday_status_id') for values in vals_list if values.get('holiday_status_id')])
            mapped_validation_type = {leave_type.id: leave_type.leave_validation_type for leave_type in leave_types}

            for values in vals_list:
                employee_id = values.get('employee_id', False)
                leave_type_id = values.get('holiday_status_id')
                # Handle automatic department_id
                if not values.get('department_id'):
                    values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})

                # Handle no_validation
                if mapped_validation_type[leave_type_id] == 'no_validation':
                    values.update({'state': 'confirm'})

                if 'state' not in values:
                    # To mimic the behavior of compute_state that was always triggered, as the field was readonly
                    values['state'] = 'confirm' if mapped_validation_type[leave_type_id] != 'no_validation' else 'draft'

                # Handle double validation
                # if mapped_validation_type[leave_type_id] == 'both':
                #     self._check_double_validation_rules(employee_id, values.get('state', False))

        holidays = super(HRLeave, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

        for holiday in holidays:
            if not self._context.get('leave_fast_create'):
                # Everything that is done here must be done using sudo because we might
                # have different create and write rights
                # eg : holidays_user can create a leave request with validation_type = 'manager' for someone else
                # but they can only write on it if they are leave_manager_id
                holiday_sudo = holiday.sudo()
                # holiday_sudo.add_follower(employee_id)
                if holiday.validation_type == 'manager':
                    holiday_sudo.message_subscribe(partner_ids=holiday.employee_id.leave_manager_id.partner_id.ids)
                # if holiday.validation_type == 'no_validation':
                    # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
                    # holiday_sudo.action_validate()
                    # holiday_sudo.message_subscribe(partner_ids=[holiday._get_responsible_for_approval().partner_id.id])
                    # holiday_sudo.message_post(body=_("The time off has been automatically approved"), subtype_xmlid="mail.mt_comment") # Message from OdooBot (sudo)
                elif not self._context.get('import_file'):
                    holiday_sudo.activity_update()
        return holidays

    # -------- Auto Create & Send Email Alpha ------
    @api.model
    def check_remind_approval(self):
        leave_obj = self.env['hr.leave']
        leave_ids = leave_obj.search([('state', '=', 'confirm')])
        for leave in leave_ids:
            leave.approval_id.write({'is_email_sent': True})
        return

    def name_get(self):
        res = []
        for leave in self:
            if self.env.context.get('short_name'):
                if leave.leave_type_request_unit == 'hour':
                    res.append((leave.id, _("%s : %.2f hours") % (leave.name or leave.holiday_status_id.name, leave.number_of_hours_display)))
                else:
                    res.append((leave.id, _("%s : %.2f days") % (leave.name or leave.holiday_status_id.name, leave.number_of_days)))
            else:
                if leave.holiday_type == 'company':
                    target = leave.mode_company_id.name
                elif leave.holiday_type == 'department':
                    target = leave.department_id.name
                elif leave.holiday_type == 'category':
                    target = leave.category_id.name
                else:
                    # target = leave.employee_id.name
                    target = leave.mncei_employee_id.nama_lengkap
                display_date = format_date(self.env, leave.date_from)
                if leave.leave_type_request_unit == 'hour':
                    if self.env.context.get('hide_employee_name') and 'mncei_employee_id' in self.env.context.get('group_by', []):
                        res.append((
                            leave.id,
                            _("%(person)s on %(leave_type)s: %(duration).2f hours on %(date)s",
                                person=target,
                                leave_type=leave.holiday_status_id.name,
                                duration=leave.number_of_hours_display,
                                date=display_date,
                            )
                        ))
                    else:
                        res.append((
                            leave.id,
                            _("%(person)s on %(leave_type)s: %(duration).2f hours on %(date)s",
                                person=target,
                                leave_type=leave.holiday_status_id.name,
                                duration=leave.number_of_hours_display,
                                date=display_date,
                            )
                        ))
                else:
                    if leave.number_of_days > 1:
                        display_date += ' ⇨ %s' % format_date(self.env, leave.date_to)
                    if self.env.context.get('hide_employee_name') and 'mncei_employee_id' in self.env.context.get('group_by', []):
                        res.append((
                            leave.id,
                            _("%(leave_type)s: %(duration).2f days (%(start)s)",
                                leave_type=leave.holiday_status_id.name,
                                duration=leave.number_of_days,
                                start=display_date,
                            )
                        ))
                    else:
                        res.append((
                            leave.id,
                            _("%(person)s on %(leave_type)s: %(duration).2f days (%(start)s)",
                                person=target,
                                leave_type=leave.holiday_status_id.name,
                                duration=leave.number_of_days,
                                start=display_date,
                            )
                        ))
        return res

    # -------- To Create Attachment ------
    def add_attachment(self, leave_id, filename=False):
        attachment = self.env['ir.attachment'].create(
            {
                'name': str(leave_id.id),
                'company_id': leave_id.mncei_employee_id.company.id,
                'public': True,
                'type': 'binary',
                'datas': filename,
                'res_model': 'hr.leave',
                'res_field': 'attachment',
                'res_id': leave_id.id
            })
        return attachment

    @api.depends_context('uid')
    def _compute_description(self):
        self.check_access_rights('read')
        self.check_access_rule('read')

        is_officer = self.user_has_groups('hr_holidays.group_hr_holidays_user')

        for leave in self:
            if is_officer or leave.user_id == self.env.user or leave.employee_id.leave_manager_id == self.env.user or leave.approve_uid == self.env.user or user_approval_ids in self.env.user.ids:
                leave.name = leave.sudo().private_name
            else:
                leave.name = '*****'

    def action_archive(self):
        self.write({'active': False})


class HrLeaveApproval(models.Model):
    _name = 'hr.leave.approval'
    _description = 'MNCEI Perdin Approval'
    _order = 'id asc'
    _rec_name = 'leave_id'

    leave_id = fields.Many2one('hr.leave', string='Leave ID', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', store=True)
    email = fields.Char(string='Email', related='user_id.login', store=True)
    jabatan = fields.Char(string='Jabatan', store=True)
    approve_date = fields.Datetime('Timestamp')
    is_email_sent = fields.Boolean('Sent')
    action_type = fields.Selection([('Approve', 'Approved'),('Reject', 'Decline')], string="Action Type", store=True)
    is_current_user = fields.Boolean('Approved', store=True)
    notes = fields.Text('Notes')
    reject_notes = fields.Text(string='Reject Notes')
    digital_signature = fields.Binary(string="Draw Signature")
    upload_signature = fields.Binary(string="Upload Signature")

    def create_push_notify(self, user_id, message):
        push_id = self.env["push.notification"].create({
            "user": user_id.id,
            "topic": "notification",
            "title": "notification person",
            'code': 'Leave',
            'action': 'approval',
            'res_id': self.leave_id.id,
            "message": message
        })
        return push_id

    def send_notify(self):
        title_value = ("Waiting Your Approval")
        message = '''Waiting Approval in leave request from %s''' % (self.leave_id.mncei_employee_id.nama_lengkap)
        mobile_token = self.user_id.mobile_token
        login = self.user_id.login
        response = push_notification(title_value, message, mobile_token, login, res_id=self)
        if response:
            self.create_push_notify(self.user_id, message)
        return
