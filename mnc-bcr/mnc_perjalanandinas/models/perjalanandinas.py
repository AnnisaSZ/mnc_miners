from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError


class perjalanandinasModels(models.Model):
    _name = 'perjalanan.dinas.requestion.module'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Perjalanan Dinas'
    _order = 'id desc'

    def get_sequence(self, company):
        sequence = self.env['ir.sequence'].with_company(company).next_by_code('perdin.code')
        return sequence

    # def _company_ids_domain(self):
    #     return [('id', 'in', self.env.user.company_ids.ids)]

    nama_karyawan = fields.Many2one('mncei.employee', string='Nama Karyawan', store=True, size=75, required=True)
    no_perdin = fields.Char(string='No.', store=True, size=25, default='#', copy=False)
    perusahaan = fields.Many2one('res.company', string="Perusahaan", store=True, size=75, required=True)
    department_id = fields.Many2one('mncei.department', string='Department', store=True, required=True)
    jabatan_id = fields.Many2one('mncei.jabatan', string='Jabatan', store=True, required=True)
    tujuan = fields.Many2one('tujuan.module', string="Tujuan", store=True, required=True, domain="[('status', '=', 'aktif')]")
    tugas = fields.Many2one('tugas.module', string="Tugas", store=True, required=True, domain="[('status', '=', 'aktif')]")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft', store=True, required=True, copy=False, tracking=True)
    attachment_ids = fields.One2many('mncei.perdin.attachment', 'perdin_id', string="Lampiran")
    type_transportation = fields.Char(
        string='Transportasi', compute='_get_type_transportation', store=True, copy=False
    )

    tgl_min_berangkat = fields.Date(string='Min. Tgl Berangkat', store=True)
    # Keberangkatan
    berangkat = fields.Datetime(string='Tanggal/Waktu', store=True)
    pesawat_berangkat = fields.Boolean(string='Pesawat', store=True)
    kereta_berangkat = fields.Boolean(string='Kereta', store=True)
    bus_berangkat = fields.Boolean(string='Bus', store=True)
    taksi_berangkat = fields.Boolean(string='Taksi', store=True)
    travel_berangkat = fields.Boolean(string='Travel', store=True)
    is_etc_berangkat = fields.Boolean(string='Dll', store=True)
    etc_berangkat = fields.Char(string='Dll', store=True)

    # Kepulangan
    kembali = fields.Datetime(string='Tanggal/Waktu', store=True)
    pesawat_kembali = fields.Boolean(string='Pesawat', store=True)
    kereta_kembali = fields.Boolean(string='Kereta', store=True)
    bus_kembali = fields.Boolean(string='Bus', store=True)
    taksi_kembali = fields.Boolean(string='Taksi', store=True)
    travel_kembali = fields.Boolean(string='Travel', store=True)
    is_etc_kembali = fields.Boolean(string='Dll', store=True)
    etc_kembali = fields.Char(string='Dll', store=True)

    # Deklarasi
    is_declaration = fields.Boolean('Deklarasi', store=True, tracking=True)

    # Add Information
    penginapan = fields.Boolean(string='Penginapan', store=True)
    one_trip = fields.Boolean(string='One Trip', store=True)
    tentative = fields.Boolean(string='Tentative', store=True)
    catatan = fields.Text(string='Catatan', size=125, store=True)
    reason_reject = fields.Text("Reason Rejected", store=True)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True)

    # Approval
    requestor_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Requestor', store=True, required=True)
    spv_id = fields.Many2one('res.users', string='Supervisor', store=True)
    head_dept_id = fields.Many2one('res.users', string='Head Department', store=True, required=True)
    head_ga_id = fields.Many2one('res.users', string='GA Department', store=True, required=True)
    hrga_id = fields.Many2one('res.users', string='HR Dept', store=True, required=True)
    head_hrga_id = fields.Many2one('res.users', string='Head HR Dept', store=True, required=True)
    direksi_id = fields.Many2one('res.users', string='Direktur', store=True, required=True)
    direksi_optional_id = fields.Many2one('res.users', string='Direktur', store=True)
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_perdin_user_rel', 'perdin_id', 'user_id',
        string='Approvals', store=True, copy=False
    )
    ga_uids = fields.Many2many(
        'res.users', 'ga_perdin_user_rel', 'ga_id', 'perdin_id',
        string='GA Users', compute='_get_ga_users', store=True
    )
    # User Approval
    approval_ids = fields.One2many('mncei.perdin.approval', 'perdin_id', string="Approval List", compute='add_approval', store=True)
    approve_uid = fields.Many2one('res.users', string='User Approve', store=True, readonly=True)
    approval_id = fields.Many2one(
        'mncei.perdin.approval',
        string='Approval', store=True, readonly=True
    )

    @api.depends('pesawat_kembali', 'kereta_kembali', 'bus_kembali', 'taksi_kembali', 'travel_kembali', 'pesawat_berangkat', 'kereta_berangkat', 'bus_berangkat', 'taksi_berangkat', 'travel_berangkat', 'etc_kembali', 'etc_berangkat')
    def _get_type_transportation(self):
        for perdin in self:
            trasport = []
            if perdin.pesawat_kembali or perdin.pesawat_berangkat:
                trasport.append('Pesawat')
            if perdin.kereta_kembali or perdin.kereta_berangkat:
                trasport.append('Kereta')
            if perdin.bus_kembali or perdin.bus_berangkat:
                trasport.append('Bus')
            if perdin.taksi_kembali or perdin.taksi_berangkat:
                trasport.append('Taksi')
            if perdin.travel_kembali or perdin.travel_berangkat:
                trasport.append('Travel')
            if perdin.etc_berangkat:
                trasport.append(perdin.etc_berangkat)
            if perdin.etc_kembali:
                trasport.append(perdin.etc_kembali)
            # Set Value
            if len(trasport) > 0:
                perdin.type_transportation = ','.join(trasport)
            else:
                perdin.type_transportation = '-'

    def _get_ga_users(self):
        for perdin in self:
            groups_ga = self.env.ref('mnc_perjalanandinas.group_perdin_mgt')
            perdin.ga_uids = [(6, 0, groups_ga.users.ids)]

    @api.depends('requestor_id', 'spv_id', 'head_dept_id', 'hrga_id', 'direksi_id', 'direksi_optional_id')
    def add_approval(self):
        for perdin in self:
            approval_obj = self.env['mncei.perdin.approval']
            if perdin.approval_ids:
                approval_list = []
                if any(approval.is_email_sent for approval in perdin.approval_ids):
                    for approval in perdin.approval_ids.filtered(lambda x: x.is_current_user or x.user_id == self.env.user):
                        approval_list.append(approval._origin.id)
                    apps_list = [perdin.hrga_id.id, perdin.head_hrga_id.id, perdin.direksi_id.id]
                    if perdin.direksi_optional_id:
                        apps_list.append(perdin.direksi_optional_id.id)
                    for approval in apps_list:
                        app_id = approval_obj.create(perdin.prepare_data_approval(approval))
                        approval_list.append(app_id.id)
                    perdin.approval_ids = [(6, 0, approval_list)]
                else:
                    approval_ids = []
                    if perdin.head_dept_id and perdin.hrga_id and perdin.direksi_id:
                        approval_ids = []
                        apps_list = [perdin.head_dept_id.id, perdin.head_ga_id.id, perdin.hrga_id.id, perdin.head_hrga_id.id, perdin.direksi_id.id]
                        if perdin.spv_id.id:
                            apps_list.insert(0, perdin.spv_id.id)
                        if perdin.direksi_optional_id:
                            apps_list.append(perdin.direksi_optional_id.id)
                        for approval in apps_list:
                            app_id = approval_obj.create(perdin.prepare_data_approval(approval))
                            approval_ids.append(app_id.id)
                    perdin.approval_ids = [(6, 0, approval_ids)]
            elif not perdin.approval_ids:
                approval_ids = []
                if perdin.head_dept_id and perdin.hrga_id and perdin.direksi_id:
                    approval_ids = []
                    apps_list = [perdin.head_dept_id.id, perdin.head_ga_id.id, perdin.hrga_id.id, perdin.head_hrga_id.id, perdin.direksi_id.id]
                    if perdin.spv_id.id:
                        apps_list.insert(0, perdin.spv_id.id)
                    if perdin.direksi_optional_id:
                        apps_list.append(perdin.direksi_optional_id.id)
                    for approval in apps_list:
                        app_id = approval_obj.create(perdin.prepare_data_approval(approval))
                        approval_ids.append(app_id.id)
                perdin.approval_ids = [(6, 0, approval_ids)]
            else:
                perdin.approval_ids = False

    def prepare_data_approval(self, user_id):
        data = {
            'user_id': user_id,
        }
        return data

    def _compute_is_creator(self):
        for record in self:
            if record.requestor_id == self.env.user:
                record.is_creator = True
            else:
                record.is_creator = False

    def _compute_is_approved(self):
        for record in self:
            if record.approve_uid == self.env.user:
                record.is_approved = True
            else:
                record.is_approved = False

    def _compute_is_ga_uid(self):
        for record in self:
            if record.head_ga_id == self.env.user:
                record.is_ga_uid = True
            else:
                record.is_ga_uid = False

    is_ga_uid = fields.Boolean(string="Is GA User", default=True, compute='_compute_is_ga_uid')
    is_creator = fields.Boolean(string="Is Creator", default=True, compute='_compute_is_creator')
    is_approved = fields.Boolean(string="Is Approved", compute='_compute_is_approved')

    @api.onchange('nama_karyawan')
    def change_company(self):
        if self.nama_karyawan:
            self.department_id = self.nama_karyawan.department
            self.jabatan_id = self.nama_karyawan.jabatan

    def action_submit(self):
        # self._check_declaration()
        approval_id = self.approval_ids.sorted(lambda x: x.id)[0]
        mail_template = self.env.ref('mnc_perjalanandinas.notification_perdin_mail_template_approved')
        if approval_id:
            mail_template.send_mail(approval_id.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': approval_id.user_id.login})
            approval_id.update({'is_email_sent': True})
            self.update({
                'state': 'waiting',
                'approve_uid': approval_id.user_id.id,
                'approval_id': approval_id.id
            })
        return

    def reset_to_draft(self):
        self.update({
            'state': 'draft'
        })
        for app_list in self.approval_ids:
            app_list.update({
                'is_email_sent': False,
                'is_current_user': False,
                'approve_date': False
            })
        return

    def action_sign_approve(self):
        signature_type = self.env.user.choice_signature
        upload_signature = False
        digital_signature = False
        upload_signature_fname = ''
        if signature_type == 'upload':
            upload_signature = self.env.user.upload_signature
            upload_signature_fname = self.env.user.upload_signature_fname
            if not upload_signature:
                raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        elif signature_type == 'draw':
            digital_signature = self.env.user.digital_signature
            if not digital_signature:
                raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        else:
            raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        return {
            'name': _("Sign & Approve"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'perdin.approval.wizard',
            'view_id': self.env.ref('mnc_perjalanandinas.perdin_approval_wizard_form').id,
            'context': {
                'default_choice_signature': signature_type,
                'default_digital_signature': digital_signature,
                'default_upload_signature': upload_signature,
                'default_upload_signature_fname': upload_signature_fname,
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            }
        }

    def open_reject(self):
        return {
            'name': _("Reason Rejected"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'perdin.approval.wizard',
            'view_id': self.env.ref('mnc_perjalanandinas.perdin_reject_view_form').id,
            'context': {
                'default_user_approval_ids': [(6, 0, self.user_approval_ids.ids)]
            }
        }

    def name_get(self):
        result = []
        for dinas in self:
            name = dinas.no_perdin
            result.append((dinas.id, name))
        return result

    def send_notif_approve(self, next_approver=False):
        mail_template = self.env.ref('mnc_perjalanandinas.notification_perdin_mail_template_approved')
        if next_approver:
            mail_template.send_mail(next_approver.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            next_approver.update({'is_email_sent': True})
        return

    # ===== Button =====
    def to_approve(self):
        self.update({
            'state': 'approve',
        })
        return

    def to_cancel(self):
        self.update({
            'state': 'cancel',
        })
        return

    @api.model
    def create(self, vals):
        params = self.env['ir.config_parameter'].sudo().get_param('duration_before_travel')
        min_travel_date = fields.Date.today() + timedelta(days=int(params))
        # Sequence
        company_id = self.env['res.company'].browse(vals.get('perusahaan'))
        sequence = self.get_sequence(company_id)
        vals.update({
            'tgl_min_berangkat': min_travel_date,
            'no_perdin': sequence
        })
        res = super(perjalanandinasModels, self).create(vals)
        if res.berangkat.date() <= min_travel_date:
            raise ValidationError(_("Keberangkatan harus dibuat minimal H - %s") % (params))
        return res

    @api.constrains('berangkat', 'kembali', 'one_trip')
    def _check_date_departure(self):
        for perdin in self:
            if perdin.berangkat.date() <= fields.Date.today():
                raise ValidationError(_("Tanggal berangkat harus lebih besar dari hari ini"))
            if not perdin.one_trip:
                if perdin.kembali.date() <= perdin.berangkat.date():
                    raise ValidationError(_("Tanggal kembali harus lebih besar dari tanggal berangkat"))

    def _check_declaration(self):
        perdin_id = self.search([('nama_karyawan', '=', self.nama_karyawan.id), ('id', '!=', self.id)], limit=1, order='id desc')
        if perdin_id:
            if not perdin_id.is_declaration:
                raise ValidationError(_("Segera lengkapi deklarasi pada perdin sebelumnya."))


class tujuanModels(models.Model):
    _name = 'tujuan.module'
    _description = 'Tujuan'

    id_tujuan = fields.Integer(
        string='ID Tujuan', related='id', store=True
    )
    tujuan = fields.Char(
        string='Tujuan', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True
    )

    def name_get(self):
        result = []
        for tujuan in self:
            name = tujuan.tujuan
            result.append((tujuan.id, name))
        return result


class tugasModels(models.Model):
    _name = 'tugas.module'
    _description = 'Tugas'

    id_tugas = fields.Integer(
        string='ID Tugas', related='id', store=True
    )
    tugas = fields.Char(
        string='Tugas', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True
    )

    def name_get(self):
        result = []
        for tugas in self:
            name = tugas.tugas
            result.append((tugas.id, name))
        return result
