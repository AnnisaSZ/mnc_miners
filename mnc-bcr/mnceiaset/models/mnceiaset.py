from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class mnceiasetModels(models.Model):
    _name = 'mnceiaset.module'
    _description = 'MNCEI ASSET Cource'
    _order = 'id desc'

    sunfish_code = fields.Char(
        string='Sunfish Code', store=True
    )
    no_aset = fields.Char(string='Nomer Aset', store=True, size=75)
    code_aset = fields.Char(string="Kode Aset", store=True, related='line_id.code_aset')
    kategori_aset = fields.Many2one('asetkategori.module',
        string="Kategori Aset", store=True, required=True, domain="[('status', '=', 'aktif')]")
    sub_categ_id = fields.Many2one(
        'sub.categ.aset',
        string='Sub Kategori', store=True, required=True, domain="[('aset_id', '=', kategori_aset)]"
    )
    sub_categ_line_id = fields.Many2one(
        'sub.categ.aset.line',
        string='Sub Kategori Line', store=True, domain="[('parent_id', '=', sub_categ_id)]"
    )
    nama_aset = fields.Char(String='Nama Aset', store=True, size=155, required=True)
    jumlah_aset = fields.Integer(string='Jumlah Aset', store=True, size=12, required=True)
    nilai_aset = fields.Integer(string='Nilai Aset', store=True, size=15, required=True)
    pemegangaset_ids = fields.One2many('pemegang.aset', 'aset_id', string='Pemegang Aset', ondelete='cascade')
    is_sunfish = fields.Boolean('Is Sunfish', store=True)
    qr_file = fields.Binary(
        string='QR'
    )
    line_id = fields.Many2one(
        'pemegang.aset',
        string='Users', compute='_get_user_aset', store=True
    )

    @api.depends('pemegangaset_ids')
    def _get_user_aset(self):
        user_aset_obj = self.env['pemegang.aset']
        for aset in self:
            if aset.pemegangaset_ids:
                if any(line.is_run for line in aset.pemegangaset_ids):
                    user_asets = aset.pemegangaset_ids.filtered(lambda x: x.is_run).sorted().ids
                    if user_asets:
                        aset.line_id = user_aset_obj.browse(user_asets[-1])
                    else:
                        aset.line_id = False
                else:
                    user_asets = aset.pemegangaset_ids.sorted().ids
                    if user_asets:
                        aset.line_id = user_aset_obj.browse(user_asets[-1])
                    else:
                        aset.line_id = False
            else:
                aset.line_id = False


    def action_qr_generate(self):
        # user_aset_obj = self.env['pemegang.aset']
        if self.pemegangaset_ids:
            # Get URL Link
            config = self.env['ir.config_parameter'].sudo()
            url_link = config.get_param('web.base.url', False)
            url = _("%s/web#action=&cids=&id=%s&menu_id=&model=mnceiaset.module&view_type=form") % (url_link, self.id)
            # Parameter
            # code_aset = ''
            # user = ''
            # Check pemegang aset
            # if any(line.is_run for line in self.pemegangaset_ids):
            #     line_id = self.pemegangaset_ids.filtered(lambda x: x.is_run).ids[-1]
            #     code_aset = user_aset_obj.browse(line_id).code_aset
            #     user = user_aset_obj.browse(line_id).employee_id.nama_lengkap
            # else:
            #     line_id = self.pemegangaset_ids.ids[-1]
            #     code_aset = user_aset_obj.browse(line_id).code_aset
            #     user = user_aset_obj.browse(line_id).employee_id.nama_lengkap
            # Dict
            # params = {
            #     'no_aset': self.no_aset,
            #     'code_aset': code_aset,
            #     'user_id': user,
            #     'categ': self.kategori_aset.kategori_aset,
            #     'sub_categ': self.sub_categ_id.name,
            #     'sub_categ_line': self.sub_categ_line_id.name or '',
            #     'detail_aset': self.nama_aset,
            # }
            # data = self.prepare_data_qr(params)
            url_link = "https://mncminers.com/web/login"
            qr_image = self.env['qr.generator'].get_qr_code(url)
            self.write({'qr_file': qr_image})
            return self.env.ref('mnceiaset.action_label_aset').report_action(self)

    def prepare_data_qr(self, data):
        return _("""Nomor Aser      : %s \nCode Aset       : %s \nUsers           : %s \nKategori        : %s \nSub Kategori    : %s \nSub Ktgr Lines  : %s \nDetail Aset     : %s \n
            """) % (data['no_aset'], data['code_aset'], data['user_id'], data['categ'], data['sub_categ'], data['sub_categ_line'], data['detail_aset'])


    @api.onchange('pemegangaset_ids.code_aset')
    def get_code_aset(self):
        # for aset in self:
        aset = self
        user_aset_obj = self.env['pemegang.aset']
        aset.code_aset = '.'
        if aset.pemegangaset_ids:
            if any(line.is_run for line in aset.pemegangaset_ids):
                line_id = aset.pemegangaset_ids.filtered(lambda x: x.is_run).ids[-1]
                aset.code_aset = user_aset_obj.browse(line_id).code_aset
            else:
                line_id = aset.pemegangaset_ids.ids[-1]
                aset.code_aset = user_aset_obj.browse(line_id).code_aset

    @api.onchange('pemegangaset_ids', 'pemegangaset_ids.is_run')
    def change_pengguna(self):
        if self.pemegangaset_ids:
            total = 0
            employees = []
            for line in self.pemegangaset_ids.filtered(lambda x: x.is_run):
                if line.employee_id.id not in employees:
                    employees.append(line.employee_id.id)
                    total += 1
            if total != self.jumlah_aset:
                return {'warning': {'title': _('Warning'), 'message': _("Pemegang Aset harus sama dengan total aset")}}

    def name_get(self):
        result = []
        for nomer_aset in self:
            name = nomer_aset.no_aset
            result.append((nomer_aset.id, name))
        return result

    @api.model
    def create(self, vals):
        if vals.get('sunfish_code') and not vals.get('no_aset'):
            sunfish_code = vals.get('sunfish_code')
            sequence = self.env['ir.sequence'].next_by_code('mncei.aset')
            vals['no_aset'] = _("%s - %s") % (sunfish_code, sequence)
            vals['is_sunfish'] = True
        res = super(mnceiasetModels, self).create(vals)
        return res


class PemegangAset(models.Model):
    _name = 'pemegang.aset'
    _description = 'Data Pemegang Aset'
    _order = 'id asc'

    aset_id = fields.Many2one('mnceiaset.module', string='Aset', ondelete='cascade')
    code_aset = fields.Char(string="Kode Aset", compute='generate_code_aset', store=True)
    pemegangaset_id = fields.Many2one('res.partner', string='Pemegang Aset')
    groups_asset_line_id = fields.Many2one('pemegang.asset.groups', string='Pemegang Aset', compute='_get_user_asset')
    # groups_id = fields.Many2one('pemegang.asset.groups', string='Pemegang Aset', compute='_get_user_asset')
    # MNC Employee
    employee_id = fields.Many2one(
        'mncei.employee',
        string='Pemegang Aset', store=True
    )
    perusahaan = fields.Many2one('res.company', string="Perusahaan")
    department = fields.Many2one('department.module', string="Department")
    # Departmen HR
    department_id = fields.Many2one('mncei.department', string="Department")

    lokasi_aset = fields.Many2one('lokasiaset.module', string="Lokasi Aset")
    kondisi_aset = fields.Many2one('kondisiaset.module', string="Kondisi Aset")
    tanggal_perolehan = fields.Date(string='Tanggal Perolehan', store=True)
    status_aset = fields.Many2one('statusaset.module', string="Status Aset")
    gambar_aset = fields.Image(string='Gambar Aset', store=True)
    catatan = fields.Char(string='Catatan', store=True)
    is_run = fields.Boolean(
        string='Digunakan', store=True, default=True
    )
    file_bast = fields.Binary(
        string='BAST',
        attachment=True, store=True
    )
    bast_filename = fields.Char(
        string='Filename BAST', store=True
    )

    @api.depends('employee_id')
    def _get_user_asset(self):
        for line in self:
            line.groups_asset_line_id = False
            if line.employee_id:
                user_asset_id = self.env['pemegang.asset.groups'].search([('employee_id', '=', line.employee_id.id)], limit=1)
                if user_asset_id:
                    line.groups_asset_line_id = user_asset_id
                else:
                    user_asset_id = self.env['pemegang.asset.groups'].create({
                        'employee_id': line.employee_id.id,
                        'name': _("%s [%s]") % (line.employee_id.nama_lengkap, line.employee_id.nip_char),
                    })
                    line.groups_asset_line_id = user_asset_id

    @api.onchange('employee_id')
    def change_department(self):
        if self.employee_id:
            if self.employee_id.department:
                self.department_id = self.employee_id.department
            if self.employee_id.company:
                self.perusahaan = self.employee_id.company

    @api.constrains('file_bast')
    def check_bast(self):
        for line in self:
            if not line.file_bast:
                raise ValidationError(_("Tolong masukan file bast"))

    @api.depends('department', 'lokasi_aset', 'aset_id', 'aset_id.kategori_aset', 'aset_id.sub_categ_id', 'aset_id.sub_categ_line_id')
    def generate_code_aset(self):
        for line in self:
            line.code_aset = False
            if line.department and line.lokasi_aset and line.aset_id:
                if line.aset_id.kategori_aset and line.aset_id.sub_categ_id:
                    code_dept = line.department.code
                    code_lokasi = line.lokasi_aset.code
                    code_categ = line.aset_id.kategori_aset.code
                    code_sub_categ = line.aset_id.sub_categ_id.code
                    code_sub_categ_line = line.aset_id.sub_categ_line_id.code
                    # Set code aset
                    if code_sub_categ_line:
                        code = _("%s%s-%s-%s-%s") % (code_lokasi, code_dept, code_categ, code_sub_categ, code_sub_categ_line)
                    else:
                        code = _("%s%s-%s-%s") % (code_lokasi, code_dept, code_categ, code_sub_categ)
                    line.code_aset = code

    @api.constrains('tanggal_perolehan')
    def _check_tgl_perolehan(self):
        for line in self:
            line_id = self.env['pemegang.aset'].search([('aset_id', '=', line.aset_id.id), ('id', '<', line.id)], order='id desc', limit=1)
            if line_id:
                if line.tanggal_perolehan:
                    if line.tanggal_perolehan <= line_id.tanggal_perolehan:
                        raise ValidationError(_("Tanggal Perolehan harus lebih besar dari tanggal perolehan pemegang aset sebelumnya"))

    @api.onchange('employee_id')
    def check_same_assets(self):
        if self.employee_id:
            asset_line_ids = self.env['pemegang.aset'].search([('employee_id', '=', self.employee_id.id), ('is_run', '=', True)], order='id desc')
            for asl in asset_line_ids:
                if self.aset_id.kategori_aset == asl.aset_id.kategori_aset and self.aset_id.sub_categ_id == asl.aset_id.sub_categ_id and self.aset_id.sub_categ_line_id == asl.aset_id.sub_categ_line_id:
                    return {'warning': {'title': _('Warning'), 'message': _("Apakah anda yakin memberikan asset tersebut ke karyawan yang sama?.")}}

    def name_get(self):
        result = []
        for used in self:
            name = used.employee_id.nama_lengkap
            result.append((used.id, name))
        return result


class lokasiasetModels(models.Model):
    _name = 'lokasiaset.module'
    _description = 'Lokasi ASSET'

    id_lokasiaset = fields.Integer(
        string='ID Lokasi Aset', related='id', store=True
    )
    lokasi_aset = fields.Char(
        string='Lokasi Aset', store=True, required=True
    )
    code = fields.Char('Kode', store=True, required=True)
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True
    )

    @api.constrains('code')
    def check_code(self):
        for lokasiaset in self:
            lok_ids = self.search([('code', '=', lokasiaset.code)])
            if len(lok_ids) > 1:
                raise ValidationError(_("Kode tidak boleh sama"))

    def name_get(self):
        result = []
        for lokasi_aset in self:
            name = lokasi_aset.lokasi_aset
            result.append((lokasi_aset.id, name))
        return result


class kondisiasetModels(models.Model):
    _name = 'kondisiaset.module'
    _description = 'Kondisi ASSET'

    id_kondisiaset = fields.Integer(
        string='ID Kondisi Aset', related='id', store=True
    )
    kondisi_aset = fields.Char(
        string='Kondisi Aset', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True
    )

    def name_get(self):
        result = []
        for kondisi_aset in self:
            name = kondisi_aset.kondisi_aset
            result.append((kondisi_aset.id, name))
        return result


class statusasetModels(models.Model):
    _name = 'statusaset.module'
    _description = 'Status ASSET'

    id_statusaset = fields.Integer(
        string='ID Status Aset', related='id', store=True
    )
    status_aset = fields.Char(
        string='Status Aset', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True
    )

    def name_get(self):
        result = []
        for status_aset in self:
            name = status_aset.status_aset
            result.append((status_aset.id, name))
        return result


class departmentModels(models.Model):
    _name = 'department.module'
    _description = 'Department'

    id_department = fields.Integer(
        string='ID Department', related='id', store=True
    )
    department = fields.Char(
        string='Department', store=True, required=True
    )
    code = fields.Char('Kode Department', store=True, required=True)
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True
    )

    @api.constrains('code')
    def check_code(self):
        for department in self:
            dept_ids = self.search([('code', '=', department.code)])
            if len(dept_ids) > 1:
                raise ValidationError(_("Kode tidak boleh sama"))

    def name_get(self):
        result = []
        for department in self:
            name = department.department
            result.append((department.id, name))
        return result
