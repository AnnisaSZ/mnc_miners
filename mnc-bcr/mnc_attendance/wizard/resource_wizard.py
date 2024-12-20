# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http


class ResourceWizard(models.TransientModel):
    _name = "resource.calendar.wizard"
    _description = "Resource Calendar Wizard"

    apply_type = fields.Selection([
        ('all_employee', 'All Employee'),
        ('employee', 'Employee'),
        ('department', 'Department'),
    ], default='all_employee', string='Apply To')
    employee_ids = fields.Many2many(
        'mncei.employee',
        string='Employee', domain="[('state', '=', 'verified')]", copy=False
    )
    department_ids = fields.Many2many(
        'mncei.department',
        string='Department', copy=False
    )
    company_ids = fields.Many2many(
        'res.company', string='Companies')
    temporary = fields.Boolean(string='Temporary')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    resource_id = fields.Many2one(
        'resource.calendar', 'Working Hours')
    loc_working_id = fields.Many2one(
        'mncei.lokasi.kerja', 'Working Location')
    # Shift
    is_shift = fields.Boolean('Shift', store=True)
    line_ids = fields.One2many('resource.calendar.wizard.line', 'resource_wizard_id', string="Line")

    def action_to_apply(self):
        domain = [('company', 'in', self.company_ids.ids), ('lokasi_kerja', '=', self.loc_working_id.id), ('state', '=', 'verified')]
        if self.is_shift:
            self.check_is_shift(domain)
        else:
            temp_work_obj = self.env['employee.shift.temp']
            if self.apply_type == 'all_employee':
                employee_ids = self.search_employee(domain)
                if employee_ids:
                    for employee_id in employee_ids:
                        if self.temporary:
                            self.check_date_period(employee_id, self.start_date, self.end_date)
                            temp_work_obj.create({
                                'mncei_employee_id': employee_id.id,
                                'working_time_id': self.resource_id.id,
                                'start_date': self.start_date,
                                'end_date': self.end_date,
                            })
                        else:
                            employee_id.write({
                                'working_time_id': self.resource_id.id
                            })
            elif self.apply_type == 'employee':
                if self.employee_ids:
                    for employee_id in self.employee_ids:
                        if self.temporary:
                            self.check_date_period(employee_id, self.start_date, self.end_date)
                            temp_work_obj.create({
                                'mncei_employee_id': employee_id.id,
                                'working_time_id': self.resource_id.id,
                                'start_date': self.start_date,
                                'end_date': self.end_date,
                            })
                        else:
                            employee_id.write({
                                'working_time_id': self.resource_id.id
                            })
            elif self.apply_type == 'department':
                domain += [('department', 'in', self.department_ids.ids)]
                employee_ids = self.search_employee(domain)
                if employee_ids:
                    for employee_id in employee_ids:
                        if self.temporary:
                            self.check_date_period(employee_id, self.start_date, self.end_date)
                            temp_work_obj.create({
                                'mncei_employee_id': employee_id.id,
                                'working_time_id': self.resource_id.id,
                                'start_date': self.start_date,
                                'end_date': self.end_date,
                            })
                        else:
                            employee_id.write({
                                'working_time_id': self.resource_id.id
                            })
        return

    def check_is_shift(self, domain=[]):
        employee_ids = []
        temp_work_obj = self.env['employee.shift.temp']
        if self.apply_type == 'all_employee':
            employee_ids = self.search_employee(domain)
        elif self.apply_type == 'department':
            domain += [('department', 'in', self.department_ids.ids)]
            employee_ids = self.search_employee(domain)

        for line in self.line_ids:
            if self.apply_type == 'employee':
                for employee_id in line.mncei_employee_ids:
                    self.check_date_period(employee_id, line.start_date, line.end_date)
                    temp_work_obj.create({
                        'is_shift': True,
                        'mncei_employee_id': employee_id.id,
                        'working_time_id': self.resource_id.id,
                        'resouce_line_id': line.resouce_line_id.id,
                        'resource_group_id': line.resource_group_id.id,
                        'start_date': line.start_date,
                        'end_date': line.end_date,
                    })
                    if not self.temporary:
                        employee_id.write({
                            'working_time_id': self.resource_id.id
                        })
            else:
                for employee_id in employee_ids:
                    self.check_date_period(employee_id, line.start_date, line.end_date)
                    temp_work_obj.create({
                        'is_shift': True,
                        'mncei_employee_id': employee_id.id,
                        'working_time_id': self.resource_id.id,
                        'resouce_line_id': line.resouce_line_id.id,
                        'resource_group_id': line.resource_group_id.id,
                        'start_date': line.start_date,
                        'end_date': line.end_date,
                    })
                    if not self.temporary:
                        employee_id.write({
                            'working_time_id': self.resource_id.id
                        })

        return True

    def search_employee(self, domain):
        employee_ids = self.env['mncei.employee'].search(domain)
        return employee_ids

    def check_date_period(self, employee, start, end):
        shift_temp = self.env['employee.shift.temp'].search([('mncei_employee_id', '=', employee.id), ('start_date', '>=', start), ('end_date', '<=', end)])
        if shift_temp:
            raise ValidationError(_("Employee %s have temp shift") % (employee.nama_lengkap))

    @api.onchange('temporary')
    def _onchange_domain_employee(self):
        if self.line_ids:
            for line in self.line_ids:
                line.temporary = self.temporary


class ResourceWizardLine(models.TransientModel):
    _name = "resource.calendar.wizard.line"

    resource_wizard_id = fields.Many2one('resource.calendar.wizard', string="Resource Wizard")
    company_ids = fields.Many2many(
        'res.company', string='Companies', related='resource_wizard_id.company_ids')
    loc_working_id = fields.Many2one(
        'mncei.lokasi.kerja', 'Working Location', related='resource_wizard_id.loc_working_id')
    temporary = fields.Boolean(string='Temporary')
    resouce_line_id = fields.Many2one('resource.calendar.attendance', string='Shift')
    resource_group_id = fields.Many2one('resource.calendar.group', string='Shift')
    start_date = fields.Date('Start')
    end_date = fields.Date('End')
    mncei_employee_ids = fields.Many2many('mncei.employee', string='Employee', ondelete='restrict')
