from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.addons.base_field_big_int.field import BigInt
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

import logging

_logger = logging.getLogger(__name__)


class MnceiEmployeeTraining(models.Model):
    _name = "mncei.employee.training"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Training"

    employee_id = fields.Many2one('mncei.employee', 'Employee', store=True)
    name = fields.Char("Nama Pelatihan", store=True)
    exp_date = fields.Date('Tgl Berakhir', store=True)
    start_date = fields.Date('Tgl Berlaku', store=True)
    certificate = fields.Binary('Sertifikat')
    certificate_filename = fields.Char('Sertifikat Filename')
    location = fields.Char('Location', required=True, store=True)
    conducted_by = fields.Char('Penyelenggara', required=True, store=True)
    total = fields.Integer(
        string='Total', store=True, compute='_calculate_date_total'
    )

    @api.constrains('start_date', 'exp_date')
    def _check_date(self):
        for training in self:
            if training.start_date > training.exp_date:
                raise ValidationError(_("Tgl Selesai harus lebih besar dari Tgl Mulai"))

    @api.depends('start_date', 'exp_date')
    def _calculate_date_total(self):
        for training in self:
            if training.start_date and training.exp_date:
                total_date = training.exp_date - training.start_date
                training.total = int(total_date.days) + 1
            else:
                training.total = 1


class MnceiLicense(models.Model):
    _name = "mncei.employee.license"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee License"

    employee_id = fields.Many2one('mncei.employee', 'Employee', store=True)
    license_no = fields.Char('License No.', store=True)
    license_name = fields.Char('License Name', store=True)
    kualf_id = fields.Many2one(
        'mncei.emp.rate',
        string='Rating/Kualifikasi', store=True, domain="[('state', '=', 'active')]"
    )
    flying_hours = fields.Integer(
        string='Jam Terbang', store=True
    )
    total = fields.Integer(
        string='Total', store=True
    )
    pic = fields.Char('PIC', store=True)
    start_date = fields.Date('Start', store=True)
    end_date = fields.Date('End', store=True)
    certificate = fields.Binary('Sertifikat')
    certificate_filename = fields.Char('Sertifikat Filename')

    @api.constrains('start_date', 'end_date')
    def _check_date(self):
        for license in self:
            if license.start_date > license.end_date:
                raise ValidationError(_("Tgl Selesai harus lebih besar dari Tgl Mulai"))
