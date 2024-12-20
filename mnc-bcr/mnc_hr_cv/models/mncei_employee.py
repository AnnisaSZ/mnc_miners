from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class MnceiEmployee(models.Model):
    _inherit = "mncei.employee"

    graduated_year = fields.Char('Graduated', store=True)
    # Passport
    passport_number = fields.Char('Passport No.', store=True, size=17)
    passport_date_issued = fields.Date('Date of Issued', store=True, size=17)
    passport_date_expired = fields.Date('Date of Expired', store=True, size=17)
    passport_place = fields.Char('Place', store=True, size=17)
    # Experience
    date_end_experience = fields.Char("Tahun Selesai", store=True)
    inside_experience = fields.Char("Jabatan Sebelumnya", store=True)
    date_end_inside_experience = fields.Char("Tahun Selesai", store=True)
    # KTP
    ktp_date_issued = fields.Date('Date of Issued', store=True, size=17)
    ktp_date_expired = fields.Date('Date of Expired', store=True, size=17)
    ktp_place = fields.Char('Place', store=True, size=17)


    @api.constrains('passport_date_issued', 'passport_date_expired', 'ktp_date_expired', 'ktp_date_issued')
    def _check_date(self):
        for employee in self:
            if employee.passport_date_issued > employee.passport_date_expired:
                raise ValidationError(_("Tgl Berakhir Passport harus lebih besar dari Tgl Dikeluarkan Passport"))
            if employee.ktp_date_issued > employee.ktp_date_expired:
                raise ValidationError(_("Tgl Berakhir KTP harus lebih besar dari Tgl Dikeluarkan KTP"))

    @api.model
    def action_my_datas(self):
        res_employee = self.env.user.mncei_employee_id
        if not res_employee:
            raise ValidationError(_("Please call HR to create your data"))
        return res_employee.id
