from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


# Department
class MnceiDepartment(models.Model):
    _name = "mncei.department"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "MNC Department"

    id_department = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Nama Department', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Jabatan
class MnceiJabatan(models.Model):
    _name = "mncei.jabatan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Jabatan"

    id_jabatan = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Nama Jabatan', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# HR Kategori
class MnceiKategori(models.Model):
    _name = "mncei.hr.kategori"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "HR Kategori"

    id_hr_categ = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Nama Kategori', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Agama
class MnceiAgama(models.Model):
    _name = "mncei.hr.agama"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Agama"

    id_agama = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Nama Agama', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Status Karyawan
class MnceiEmployeeStatus(models.Model):
    _name = "mncei.emp.status"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Status"

    id_emp_status = fields.Integer(
        string='ID', related='id', store=True
    )
    is_kontrak = fields.Boolean('Period', store=True)
    name = fields.Char(
        string='Status Karyawan', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Pajak
class MnceiPajak(models.Model):
    _name = "mncei.status.pajak"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Status Pajak"

    id_status_pajak = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Status Pajak', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Status Pendidikan
class MnceiStatusPendidik(models.Model):
    _name = "mncei.status.pendidikan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Status Pendidikan"

    id_pendidikan = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Jenjang Pendidikan', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Lokasi Kerja
class MnceiLokasiKerja(models.Model):
    _name = "mncei.lokasi.kerja"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Lokasi Kerja"

    id_lokasi = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Lokasi', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Golongan
class MnceiEmpGolongan(models.Model):
    _name = "mncei.employee.golongan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Status Pajak"

    id_emp_golongan = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Nama Golongan', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Grade
class MnceiGrade(models.Model):
    _name = "mncei.grade"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Grade"

    id_grade = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Grade', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Tingkat Pendidikan
class MnceiPendidikan(models.Model):
    _name = "mncei.nama.pendidikan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Education"

    id_institusi = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Nama Institusi/Universitas', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Gol Darah
class MnceiGolDarah(models.Model):
    _name = "mncei.gol.darah"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Education"

    id_gol_darah = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Golongan Darah', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)


# Kualifikasi
class MnceiRate(models.Model):
    _name = "mncei.emp.rate"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rating/Kualifikasi"

    id_emp_rate = fields.Integer(
        string='ID', related='id', store=True
    )
    name = fields.Char(
        string='Rating/Kualifikasi', store=True, required=True
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('deactive', 'Non Active')
    ], default='active', store=True, string="Status", required=True)
