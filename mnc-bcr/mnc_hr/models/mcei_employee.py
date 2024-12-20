from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.addons.base_field_big_int.field import BigInt
# from datetime import timedelta
from dateutil.relativedelta import relativedelta

import re
import logging

_logger = logging.getLogger(__name__)


class MnceiEmployee(models.Model):
    _name = "mncei.employee"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "HR Employee"
    _rec_name = "nama_lengkap"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    # Data Employee
    nama_lengkap = fields.Char(string='Nama Lengkap', store=True, size=75, required=True, tracking=True)
    tempat_lahir = fields.Char(string='Tempat Lahir', size=75, required=True, store=True, help="Tempat Lahir Karyawan")
    nama_pasangan = fields.Char(string='Nama Pasangan', size=75, store=True, help="Tempat Lahir Karyawan")
    tgl_lahir = fields.Date("Tanggal Lahir", store=True, required=True, tracking=True)
    no_ktp = BigInt('No. KTP', store=True, compute='_convert_value', readonly=False, digits=(16, 0), tracking=True)
    no_kk = BigInt("No KK", store=True, compute='_convert_value', readonly=False)
    no_tlp = fields.Char("No Telp", store=True, size=25)
    npwp = fields.BigInt("NPWP", compute='_convert_value', store=True, size=25)
    no_hp_pasangan = fields.Char("No HP Pasangan", store=True, size=25)
    alamat = fields.Text("Alamat Tinggal", required=True, store=True, size=25)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    foto_pegawai = fields.Image("Foto Pegawai", store=True, required=True)
    jenis_kelamin = fields.Selection([
        ('L', 'Laki Laki'),
        ('P', 'Perempuan'),
    ], store=True, string='Jenis Kelamin', required=True)
    status_perkwn = fields.Selection([
        ('kawin', 'Kawin'),
        ('belum_kawin', 'Belum Kawin'),
        ('cerai', 'Cerai'),
    ], store=True, default='belum_kawin', string='Status Perkawinan', required=True)
    weight = fields.Integer('Weight', store=True)
    height = fields.Integer('Height', store=True)
    # M2O
    department = fields.Many2one(
        'mncei.department',
        string='Div/Dept', store=True, tracking=True, required=True, domain="[('state', '=', 'active')]"
    )
    jabatan = fields.Many2one(
        'mncei.jabatan',
        string='Jabatan', store=True, tracking=True, required=True, domain="[('state', '=', 'active')]"
    )
    kategori = fields.Many2one(
        'mncei.hr.kategori',
        string='Kategori', store=True, tracking=True, domain="[('state', '=', 'active')]"
    )
    agama = fields.Many2one(
        'mncei.hr.agama',
        string='Agama', store=True, required=True, domain="[('state', '=', 'active')]"
    )
    status_karyawan = fields.Many2one(
        'mncei.emp.status',
        string='Status Karyawan', store=True, tracking=True, required=True, domain="[('state', '=', 'active')]"
    )
    status_penddk = fields.Many2one(
        'mncei.status.pendidikan',
        string='Tingkat Pendidikan', store=True, required=True, domain="[('state', '=', 'active')]"
    )
    lokasi_kerja = fields.Many2one(
        'mncei.lokasi.kerja',
        string='Lokasi Kerja', store=True, required=True, domain="[('state', '=', 'active')]"
    )
    golongan = fields.Many2one(
        'mncei.employee.golongan',
        string='Golongan', store=True, tracking=True, domain="[('state', '=', 'active')]"
    )
    status_pajak = fields.Many2one(
        'mncei.status.pajak',
        string='Status Pajak', store=True, tracking=True, required=True, domain="[('state', '=', 'active')]"
    )
    grade = fields.Many2one(
        'mncei.grade',
        string='Grade', store=True, tracking=True, domain="[('state', '=', 'active')]"
    )
    education = fields.Many2one(
        'mncei.nama.pendidikan',
        string='Nama Pendidikan', store=True, required=True, domain="[('state', '=', 'active')]"
    )
    gol_darah = fields.Many2one(
        'mncei.gol.darah',
        string='Golongan Darah', store=True, required=True, domain="[('state', '=', 'active')]"
    )
    kualf_id = fields.Many2one(
        'mncei.emp.rate',
        string='Rating/Kualifikasi', store=True, domain="[('state', '=', 'active')]"
    )
    # Information Company
    # Date
    tgl_masuk = fields.Date('Tanggal Masuk', store=True, help="Tanggal Karyawan Bergabung", required=True)
    tgl_tetap = fields.Date('Tanggal Tetap', store=True, help="Tanggal Karyawan Status Tetap")
    kontrak_berakhir = fields.Date('Kontrak Berakhir', store=True, help="Tanggal Kontrak Karyawan Berakhir")

    # Computed Date
    work_exp_year = fields.Char('Lama Bekerja(Years)', compute='calculated_date_info', store=True)
    work_exp_month = fields.Char('Lama Bekerja(Months)', compute='calculated_date_info', store=True)
    age_year = fields.Char('Usia(Years)', compute='calculated_age', store=True)
    age_month = fields.Char('Usia(Months)', compute='calculated_age', store=True)
    pension_one_year = fields.Char('1 Tahun Pensiun', compute='calculated_age', store=True)

    date_of_pension = fields.Date('Tanggal Pensiun', compute='calculated_age', store=True)
    date_one_year_pension = fields.Date('Tanggal 1 Tahun Pensiun', compute='calculated_age', store=True)

    remaks_1 = fields.Char('Remaks', store=True)
    company = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, domain=_company_ids_domain, store=True, required=True, tracking=True)
    # No Penting
    nip = fields.Integer("NIP Int", compute='_convert_value', size=25, store=True)
    nip_baru = fields.Integer("NIP Baru Int", compute='_convert_value', store=True, size=25)
    jamsostek = fields.Char("Jamsostek Pegawai", store=True, size=25, required=True)
    kjp = fields.Char("BPJS Ketenagakerjaan", store=True, size=25, required=True)
    bpjs_kes = fields.Char("BPJS Kesehatan", store=True, size=25, required=True)
    sk_pengangkatan_no = fields.Char("No. SK", store=True, size=75)

    email = fields.Char("Email", store=True, size=55, required=True)
    pengalaman_kerja = fields.Char("Pengalaman", store=True, size=55, help="Pengalaman di PT Sebelumnya, Tulis Nama Perusahaan")
    year_of_pension = fields.Char("Tahun Pensiun", compute='calculated_age', store=True, size=4)
    remaks_2 = fields.Text(
        string='Remaks',
    )

    def get_groups(self):
        group_id = self.env.ref('mnc_hr.group_hr_mgr')
        return group_id.id

    hr_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, store=True)
    group_hr_id = fields.Many2one('res.groups', default=get_groups, store=True)

    # Fields convertor parameter
    nip_char = fields.Char('NIP', required=True, size=16, store=True, tracking=True)
    nip_baru_char = fields.Char('NIP Baru', size=16, store=True, tracking=True)
    no_ktp_char = fields.Char('No KTP', size=16, required=True, store=True)
    no_kk_char = fields.Char('No KK', size=16, store=True)
    npwp_char = fields.Char('NPWP', size=16, required=True, store=True)
    is_kontrak = fields.Boolean('Kontrak', store=True, compute='_get_state_employee')

    @api.depends('status_karyawan')
    def _get_state_employee(self):
        for emp in self:
            # state_contract = self.env.ref('mnc_hr.status_kontrak')
            # if emp.status_karyawan == state_contract:
            if emp.status_karyawan.is_kontrak:
                emp.is_kontrak = True
            else:
                emp.is_kontrak = False

    # Additional Based on Wise Apps

    parent_name = fields.Char(
        string='Nama Orang Tua',
    )
    no_wa = fields.Char(
        string='WA', store=True
    )
    bbm = fields.Char(
        string='BBM', store=True
    )
    no_telp2 = fields.Char('No Telp 2', store=True)
    # Head User's
    head_user1 = fields.Many2one('mncei.employee', 'Atasan Langsung', store=True)
    head_user2 = fields.Many2one('mncei.employee', 'Department Head', store=True)
    head_user3 = fields.Many2one('mncei.employee', 'Head User 3', store=True)
    # Director
    director_1 = fields.Many2one('mncei.employee', 'Director 1', store=True)
    director_2 = fields.Many2one('mncei.employee', 'Director 2', store=True)
    director_3 = fields.Many2one('mncei.employee', 'President Director', store=True)

    # Additional

    sk_pengangkatan_file = fields.Binary('Dokumen SK', store=True)
    sk_pengangkatan_filename = fields.Char('SK Pengangkatan Filename', store=True)

    # Resign
    active = fields.Boolean('Active', default=True, store=True)
    tgl_resign = fields.Date('Tanggal Resign', store=True)
    reason_resign = fields.Text('Alasan Resign', store=True)
    clearin_sheet_file = fields.Binary('Clearin Sheet')
    clearin_sheet_filename = fields.Char('Clearin Sheet')

    # Ikatan Dinas
    is_ikatan_dinas = fields.Boolean('Ikatan Dinas', store=True)
    dinas_start = fields.Date('Tgl Masuk', store=True)
    dinas_end = fields.Date('Tgl Selesai', store=True)
    certificate = fields.Binary('Dokumen Perjanjian')
    certificate_filename = fields.Char('Dok. Perjanjian Filename')

    # Training
    emp_training_ids = fields.One2many('mncei.employee.training', 'employee_id', store=True)
    # License
    license_ids = fields.One2many('mncei.employee.license', 'employee_id', store=True)
    total_hours = fields.Integer("Total Hours", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('verified', 'Verified'),
    ], default='draft', store=True, tracking=True, required=True)
    is_revise = fields.Boolean("Revise")
    revisi_notes = fields.Text("Revisi Notes", tracking=True)

    # Button Update
    def action_review(self):
        for employee in self:
            employee.update({
                'is_revise': False,
                'state': 'review'
            })

    def action_approve(self):
        for employee in self:
            employee.update({
                'is_revise': False,
                'state': 'verified'
            })

    def action_revise(self):
        return {
            'name': _("Revise Reason"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'employee.resign.wizard',
            'view_id': self.env.ref('mnc_hr.revise_information_wizard_form').id,
        }

    # Funct untuk convert int > str, dengan tujuan untuk menghilangkan (,) pada show type int
    # @api.depends('nip_char', 'nip_baru_char', 'npwp_char', 'no_ktp_char', 'no_kk_char')
    def _convert_value(self):
        for rec in self:
            # if rec.nip_char:
            #     params = rec._check_type_data(rec.nip_char)
            #     if params:
            #         rec.nip = int(rec.nip_char)
            # if rec.nip_baru_char:
            #     params = rec._check_type_data(rec.nip_baru_char)
            #     if params:
            #         rec.nip_baru = int(rec.nip_baru_char)
            # No KTP
            # if rec.no_ktp_char:
            #     params = rec._check_type_data(rec.no_ktp_char)
            #     if params:
            #         rec.no_ktp = int(rec.no_ktp_char)
            # NPWP
            if rec.npwp_char:
                params = rec._check_type_data(rec.npwp_char)
                if params:
                    rec.npwp = int(rec.npwp_char)
            # No KK
            if rec.no_kk_char:
                params = rec._check_type_data(rec.no_kk_char)
                if params:
                    rec.no_kk = int(rec.no_kk_char)

    # Method check type data, must be integer
    def _check_type_data(self, data):
        pattern = r'^[0-9]+$'
        if data and not re.match(pattern, data):
            raise ValidationError('Field hanya boleh berisi angka.')
        else:
            return True

    @api.constrains('no_tlp')
    def _check_phone(self):
        pattern = r'^[0-9]+$'
        for rec in self:
            if rec.no_tlp and not re.match(pattern, rec.no_tlp):
                raise ValidationError('Phone hanya boleh berisi angka.')

    #########################################
    def name_get(self):
        result = []
        for emp in self:
            name = _("%s - [%s]") % (emp.nama_lengkap, emp.nip_char)
            result.append((emp.id, name))
        return result

    @api.depends('tgl_masuk')
    def calculated_date_info(self):
        for emp in self:
            emp.work_exp_year = False
            if emp.tgl_masuk:
                # Get Days
                number_of_days = (fields.Date.today() - emp.tgl_masuk)
                # Calculating years
                years = number_of_days.days // 365
                # Calculating months
                months = (number_of_days.days - years * 365) // 30
                # Import result
                emp.work_exp_year = years
                emp.work_exp_month = months

    @api.depends('tgl_lahir')
    def calculated_age(self):
        for emp in self:
            emp.age_year = False
            emp.age_month = False
            emp.date_of_pension = False
            emp.date_one_year_pension = False
            today = fields.Date.today()
            if emp.tgl_lahir:
                pension_year = emp.tgl_lahir + relativedelta(years=55)
                emp.date_of_pension = pension_year
                emp.date_one_year_pension = pension_year - relativedelta(years=1)
                # Get pension year
                emp.year_of_pension = str(pension_year.year)
                emp.pension_one_year = str((pension_year - relativedelta(years=1)).year)
                # Calculate birthday
                number_of_days = (today - emp.tgl_lahir)
                years = number_of_days.days // 365
                months = (number_of_days.days - years * 365) // 30
                # result
                emp.age_year = years
                emp.age_month = months

    def reminder_exp_status_emp(self):
        employee_ids = self.env['mncei.employee'].search([('status_karyawan.name', 'ilike', 'PKWT'), ('state', '=', 'verified')])
        template_id = self.env.ref('mnc_hr.email_template_reminder_contract')
        for employee in employee_ids:
            if employee.kontrak_berakhir:
                total_reminder = (employee.kontrak_berakhir - fields.Date.today()).days
                if total_reminder == 60:
                    user_ids = []
                    user_input = self.env.ref('group_hr_user')
                    if employee.group_hr_id.users.filtered(lambda x: employee.company.id in x.company_ids.ids):
                        for user_id in employee.group_hr_id.users:
                            user_ids.append(user_id)
                    if user_input.users.filtered(lambda x: employee.company.id in x.company_ids.ids):
                        for user_id in user_input.users:
                            if user_id not in user_ids:
                                user_ids.append(user_id)
                    for user in user_ids:
                        template_id.send_mail(employee.id, force_send=True, email_values={'email_to': user.login}, raise_exception=True)
        return

    @api.constrains('tgl_masuk', 'tgl_tetap', 'kontrak_berakhir')
    def _check_tgl_karyawan(self):
        for emp in self:
            if emp.tgl_masuk >= fields.Date.today():
                raise ValidationError(_("Tanggal Masuk Harus lebih kecil atau sama dengan hari ini"))
            else:
                if emp.kontrak_berakhir:
                    if emp.tgl_masuk >= emp.kontrak_berakhir:
                        raise ValidationError(_("Kontrak Berakhir Harus lebih besar dari Tanggal Masuk"))
                if emp.tgl_tetap:
                    if emp.tgl_masuk >= emp.tgl_tetap:
                        raise ValidationError(_("Tanggal Tetap Harus lebih besar dari tanggal masuk"))

    @api.constrains('tgl_lahir', 'no_ktp')
    def _check_data_employee(self):
        for emp in self:
            if emp.tgl_lahir and emp.no_ktp:
                employee_id = self.search([('tgl_lahir', '=', emp.tgl_lahir), ('no_ktp', '=', emp.no_ktp), ('id', '!=', emp.id)], limit=1)
                if employee_id:
                    raise ValidationError(_("Tgl dan NIK Sama dengan Employee %s-[%s], Mohon dicek kembali.") % (employee_id.nama_lengkap, employee_id.nip_char))

    def calculated_date_employee(self):
        employee_ids = self.env['mncei.employee'].search([])
        for employee in employee_ids:
            employee.calculated_date_info()
            employee.calculated_age()

    # Button Resign
    def action_resign(self):
        return {
            'name': _("Resign Information"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'employee.resign.wizard',
            'view_id': self.env.ref('mnc_hr.resign_information_wizard_form').id,
        }

    def action_active(self):
        self.write({'active': True})
        return

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        domain += ['|', ('nama_lengkap', operator, name), ('nip', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()
