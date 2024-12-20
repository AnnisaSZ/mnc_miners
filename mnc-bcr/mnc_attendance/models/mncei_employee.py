from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime

from ..controllers.main import float_to_time_str


class MnceiEmployee(models.Model):
    _inherit = "mncei.employee"

    working_time_id = fields.Many2one('resource.calendar', string='Working Time', ondelete='restrict')
    shift_temp_ids = fields.One2many('employee.shift.temp', 'mncei_employee_id', string='Shift Temporary')
    wdms_code = fields.Char(string='WDMS Code', store=True, required=True, help="Gabungan Bisnis Unit Code & NIK")
    roster_id = fields.Many2one(
        'res.roster', 'Roster', store=True)

    def get_attendance_data_by_company(self, company_id, start_date, end_date):
        attendance_obj = self.env['hr.attendance']
        attendance_data = []
        # for employee_id in employee_ids:
        employees = self.env['mncei.employee'].search([('company', '=', company_id)])
        # employees = self.env['mncei.employee'].search([('id', '=', 3207)])
        # start = '%s 00:00:00' % (start_date)
        # end = '%s 23:00:00' % (end_date)
        start = datetime.combine(start_date, datetime.min.time()) - timedelta(hours=7)
        end = datetime.combine(end_date, datetime.max.time()) - timedelta(hours=7)
        for employee in employees:
            domain = [('mncei_employee_id', '=', employee.id)]
            # Check In
            domain_ci = domain + [('check_in', '>=', start), ('check_in', '<=', end)]
            attendance_ci = self.env['hr.attendance'].sudo().search(domain_ci)
            # Check Out
            domain_co = domain + [('check_out', '>=', start), ('check_out', '<=', end)]
            attendance_co = self.env['hr.attendance'].sudo().search(domain_co)
            merged_set = set(attendance_ci).union(set(attendance_co))
            # Mengonversi kembali set ke daftar
            attendance_ids = list(merged_set)
            list_attendance = []
            # Add just id
            if len(attendance_ids) > 0:
                # for att in attendance_ids.sorted(lambda x: x.id):
                for att in sorted(attendance_ids, key=lambda x: x.id):
                    list_attendance.append({
                        'create_date': (att.check_in + timedelta(hours=7)).strftime('%d/%m/%Y') if att.check_in else (att.check_out + timedelta(hours=7)).strftime('%d/%m/%Y'),
                        'check_in': (att.check_in + timedelta(hours=7)).strftime('%H:%M') if att.check_in else '-',
                        'type_ci': dict(attendance_obj._fields['type_ci'].selection).get(att.type_ci),
                        'check_out': (att.check_out + timedelta(hours=7)).strftime('%H:%M') if att.check_out else '-',
                        'type_co': dict(attendance_obj._fields['type_co'].selection).get(att.type_co),
                        'overtime': float_to_time_str(att.overtime),
                        'working_hours': float_to_time_str(att.worked_hours) if att.worked_hours else "00:00:00",
                    })
            attendance_list_sorted = sorted(list_attendance, key=lambda x: datetime.strptime(x['create_date'], '%d/%m/%Y'))
            attendance_data.append({
                'employee_id': employee.id,
                'attendance_ids': attendance_list_sorted,
            })

        return attendance_data, employees.ids

    def get_attendance_data_by_employee(self, employee_ids, start_date, end_date):
        attendance_obj = self.env['hr.attendance']
        attendance_data = []
        for employee_id in employee_ids:
            employees = self.env['mncei.employee'].search([('id', '=', employee_id)])
            # employees = self.env['mncei.employee'].search([('id', '=', 3207)])
            # start = '%s 00:00:00' % (start_date)
            # end = '%s 23:00:00' % (end_date)
            start = datetime.combine(start_date, datetime.min.time()) - timedelta(hours=7)
            end = datetime.combine(end_date, datetime.max.time()) - timedelta(hours=7)
            for employee in employees:
                domain = [('mncei_employee_id', '=', employee.id)]
                # Check In
                domain_ci = domain + [('check_in', '>=', start), ('check_in', '<=', end)]
                attendance_ci = self.env['hr.attendance'].sudo().search(domain_ci)
                # Check Out
                domain_co = domain + [('check_out', '>=', start), ('check_out', '<=', end)]
                attendance_co = self.env['hr.attendance'].sudo().search(domain_co)
                merged_set = set(attendance_ci).union(set(attendance_co))
                # Mengonversi kembali set ke daftar
                attendance_ids = list(merged_set)
                list_attendance = []
                # Add just id
                if len(attendance_ids) > 0:
                    # for att in attendance_ids.sorted(lambda x: x.id):
                    for att in sorted(attendance_ids, key=lambda x: x.id):
                        list_attendance.append({
                            'create_date': (att.check_in + timedelta(hours=7)).strftime('%d/%m/%Y') if att.check_in else (att.check_out + timedelta(hours=7)).strftime('%d/%m/%Y'),
                            'check_in': (att.check_in + timedelta(hours=7)).strftime('%H:%M') if att.check_in else '-',
                            'type_ci': dict(attendance_obj._fields['type_ci'].selection).get(att.type_ci),
                            'check_out': (att.check_out + timedelta(hours=7)).strftime('%H:%M') if att.check_out else '-',
                            'type_co': dict(attendance_obj._fields['type_co'].selection).get(att.type_co),
                            'overtime': float_to_time_str(att.overtime),
                            'working_hours': float_to_time_str(att.worked_hours) if att.worked_hours else "00:00:00",
                        })
                attendance_list_sorted = sorted(list_attendance, key=lambda x: datetime.strptime(x['create_date'], '%d/%m/%Y'))
                attendance_data.append({
                    'employee_id': employee.id,
                    'attendance_ids': attendance_list_sorted,
                })
        return attendance_data, employee_ids

    def get_working_time(self, date_start):
        attendance_id = self.shift_temp_ids.filtered(lambda x: x.start_date <= date_start and x.end_date >= date_start)

        if attendance_id:
            working_time = attendance_id.working_time_id
        else:
            working_time = self.working_time_id
        return working_time

    def get_all_children_of_parent(self):
        direct_children = self.env['mncei.employee'].search([('head_user1', '=', self.id)])
        # List to hold all child records
        all_children = direct_children
        # Recursively get children of children
        for child in direct_children:
            child_children = child.get_all_children_of_parent()
            all_children += child_children

        return all_children

    @api.model
    def check_today_birthdays(self):
        today = fields.Date.today()
        employee_ids = self.search([('state', '=', 'verified')])
        birthday_employees = employee_ids.filtered(lambda p: p.tgl_lahir and p.tgl_lahir.month == today.month and p.tgl_lahir.day == today.day)

        for employee in birthday_employees:
            template_to_user = self.env.ref('mnc_attendance.notification_birthday_user')
            nama = employee.nama_lengkap
            template_to_direct = self.env.ref('mnc_attendance.notification_birthday_direct_user').with_context(dbname=self._cr.dbname, invited_users=nama)
            template_to_user.send_mail(employee.id, force_send=True)
            # ================== to direct user ==================
            if employee.head_user1:
                template_to_direct.send_mail(employee.head_user1.id, force_send=True, email_values={'email_to': employee.head_user1.email})
            if employee.head_user2:
                template_to_direct.send_mail(employee.head_user2.id, force_send=True, email_values={'email_to': employee.head_user2.email})
            # to BOD
            if employee.director_1:
                template_to_direct.send_mail(employee.director_1.id, force_send=True, email_values={'email_to': employee.director_1.email})
            if employee.director_2:
                template_to_direct.send_mail(employee.director_2.id, force_send=True, email_values={'email_to': employee.director_2.email})
            if employee.director_3:
                template_to_direct.send_mail(employee.director_3.id, force_send=True, email_values={'email_to': employee.director_3.email})
            # You can add any additional logic here, e.g., sending a birthday greeting
            print(f"Happy Birthday to {employee.nama_lengkap}!")

        return birthday_employees

    @api.model
    def check_today_work_anniv(self):
        today = fields.Date.today()
        employee_ids = self.search([('state', '=', 'verified')])
        birthday_employees = employee_ids.filtered(lambda p: p.tgl_masuk and p.tgl_masuk.month == today.month and p.tgl_masuk.day == today.day)

        for employee in birthday_employees:
            nama = employee.nama_lengkap
            total_working = (today.year - employee.tgl_masuk.year)
            template_to_user = self.env.ref('mnc_attendance.notification_work_anniv_user').with_context(dbname=self._cr.dbname, invited_users=nama, total_working=total_working)
            template_to_direct = self.env.ref('mnc_attendance.notification_work_anniv_direct_user').with_context(dbname=self._cr.dbname, invited_users=nama, total_working=total_working)
            template_to_user.send_mail(employee.id, force_send=True, email_values={'email_to': employee.email})
            # ================== to direct user ==================
            if employee.head_user1:
                template_to_direct.send_mail(employee.head_user1.id, force_send=True, email_values={'email_to': employee.head_user1.email})
            if employee.head_user2:
                template_to_direct.send_mail(employee.head_user2.id, force_send=True, email_values={'email_to': employee.head_user2.email})
            # to BOD
            if employee.director_1:
                template_to_direct.send_mail(employee.director_1.id, force_send=True, email_values={'email_to': employee.director_1.email})
            if employee.director_2:
                template_to_direct.send_mail(employee.director_2.id, force_send=True, email_values={'email_to': employee.director_2.email})
            if employee.director_3:
                template_to_direct.send_mail(employee.director_3.id, force_send=True, email_values={'email_to': employee.director_3.email})
            # You can add any additional logic here, e.g., sending a birthday greeting
            print(f"Happy Birthday to {employee.nama_lengkap}!")

        return birthday_employees

    # Domain Employee set apply in Working Time
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        context = self._context
        args = args or []
        domain = []
        if context.get('working_time'):
            if not context.get('temporary'):
                domain += [('company', 'in', context.get('company_ids')[0][2]), ('lokasi_kerja', '=', context.get('working_location')), ('state', '=', 'verified'), '|', ('nama_lengkap', operator, name), ('nip', operator, name)]
                print("Temporary")
            else:
                domain += [('state', '=', 'verified'), '|', ('nama_lengkap', operator, name), ('nip', operator, name)]
            rec = self.search(domain + args, limit=limit)
            return rec.name_get()
        else:
            res = super(MnceiEmployee, self).name_search(name, args=args, operator=operator, limit=limit)
            return res


class MnceiEmployeeShift(models.Model):
    _name = "employee.shift.temp"

    active = fields.Boolean('Active', default=True, store=True)
    mncei_employee_id = fields.Many2one('mncei.employee', string='Employee', ondelete='restrict', store=True)
    resouce_id = fields.Many2one('resource.calendar', string='Resource', ondelete='restrict', store=True)
    working_time_id = fields.Many2one('resource.calendar', string='Working Time', ondelete='restrict', store=True)
    is_shift = fields.Boolean('Is Shift', related='working_time_id.is_shift', store=True)
    resouce_line_id = fields.Many2one('resource.calendar.attendance', string='Shift', domain="[('calendar_id', '=', working_time_id)]", ondelete='restrict')
    start_date = fields.Date('Start', store=True)
    end_date = fields.Date('End', store=True)
    resource_group_id = fields.Many2one('resource.calendar.group', string='Shift', domain="[('resouce_id', '=', working_time_id)]", ondelete='restrict', store=True)
