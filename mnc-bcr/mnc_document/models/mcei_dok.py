from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
import logging
import re


_logger = logging.getLogger(__name__)


class MnceiBaseDokumen(models.Model):
    _name = "mncei.doc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Legal Dokumen"
    _order = 'id desc'

    # Information
    active = fields.Boolean('Active', default=True, store=True)
    document_name = fields.Char("Document Name", size=100, store=True, required=True)
    document_number = fields.Char("Document Number", size=45, store=True, required=True, copy=False)
    description = fields.Text("Description", size=225, store=True, help="Penjelasan tentang dokumen")
    url_document = fields.Char("URL", size=150, default="/", store=True, help="Penyimpanan softcopy")
    pic_phone = fields.Char("Phone No.", size=16, store=True, required=True, help="Nomor telepon penanggung jawab dokumen")
    email_reminder = fields.Char("Email Reminder", size=150, store=True)
    id_document = fields.Integer(default=1, string='Document', store=True)
    rak = fields.Selection([
        ('Rak_1', 'Rak 1'),
        ('Rak_2', 'Rak 2'),
        ('Rak_3', 'Rak 3'),
        ('Rak_4', 'Rak 4'),
        ('Rak_5', 'Rak 5')
    ], default='Rak_1', required=True, store=True, string='Partition', tracking=True)
    # M2O
    company = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id, store=True, required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', compute='_get_employee_id', store=True)
    pic = fields.Many2one('res.users', 'PIC', default=lambda self: self.env.user, store=True, required=True, copy=False)
    periode_reminder = fields.Many2one('mncei.doc.period', 'Periode', store=True, required=True, domain="[('state', '=', 'active')]", ondelete='cascade')
    document_status = fields.Many2one('mncei.doc.status', 'State', tracking=True, store=True, required=True, domain="[('state', '=', 'active'), ('is_dokumen', '=', True)]")
    # O2M
    periods_times_ids = fields.One2many('mncei.periode.reminder', 'document_id', string="Periode Time", store=True, copy=False)
    email_remind_ids = fields.One2many('mncei.mail.reminder', 'document_id', string="Emails", store=True, copy=False)
    # Information Date
    release_date = fields.Date("Agreement Date", store=True, required=True, help="Tanggal dokumen terbit")
    expired_date = fields.Date("Agreement End Date", store=True, required=True, help="Tanggal masa berlaku dokumen")
    # Notes,
    # reminder date akan otomatis dikirim dengan kondisi today => tgl reminder
    reminder_date = fields.Date("Reminder Date", store=True, required=True, help="Tanggal mulai mengirimkan dokumen")
    # remaks_process = fields.Text(
    #     string='Remarks', size=155, store=True
    # )
    # remaks_release = fields.Text(
    #     string='Remarks', size=155, store=True
    # )
    # Parameter
    # is_netral = fields.Boolean('Netral', compute='check_state', store=True)
    # is_process = fields.Boolean('Process', compute='check_state', store=True)
    # is_release = fields.Boolean('Release', compute='check_state', store=True)

    # =======New Fields=========
    category = fields.Selection([
        ('baru', 'Baru'),
        ('perpanjangan', 'Perpanjangan'),
        ('pengakhiran', 'Pengakhiran')
    ], default='baru', store=True, required=True, string='Category')
    location_doc_id = fields.Many2one('mncei.hardcopy.loc', 'Lokasi Dokumen', store=True, required=True, size=250)
    parties = fields.Char("The Parties", size=50, store=True, required=True)
    # To Delete
    type_document = fields.Selection([
        ('perjanjian', 'Perjanjian'),
        ('perizinan', 'Perizinan')
    ], store=True, string='Document Type')
    document_category = fields.Many2one('mncei.doc.categ', 'Category', store=True, domain="[('state', '=', 'active')]")
    hardcopy_document = fields.Char("Hardcopy Location", size=150, store=True, help="Penyimpanan hard dokumen")
    tracking_document_ids = fields.One2many('hr.resume.line', 'parent_doc_id', 'Tracking', store=True)
    resume_line_id = fields.Many2one('hr.resume.line.type', 'Resume', compute='_get_resume_data')

    @api.depends('document_number')
    def _get_resume_data(self):
        for document in self:
            resume_id = self.env.ref('mnc_document.resume_type_tracking_document')
            document.resume_line_id = resume_id

    # @api.depends('document_number')
    def _get_employee_id(self):
        for document in self:
            employee_id = self.env['hr.employee'].browse(1)
            document.employee_id = employee_id

    # Function
    # Cek Status Document
    # @api.depends('document_status')
    # def check_state(self):
    #     for legal in self:
    #         legal.is_netral = True
    #         legal.is_process = False
    #         legal.is_release = False
    #         if legal.document_status:
    #             # Check Condition
    #             state_name = legal.document_status.document_status
    #             if 'Process' in state_name or 'process' in state_name:
    #                 legal.is_process = True
    #                 legal.is_netral = False
    #             if 'Release' in state_name or 'release' in state_name:
    #                 legal.is_release = True
    #                 legal.is_netral = False

    def add_email(self):
        self.ensure_one()
        context = {
            'default_legal_id': self.id
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'mnc.input.email.wizard',
            'view_id': self.env.ref('mnc_document.input_emails_wizard_form').id,
            'context': context,
        }

    # Split Email By list when create or write
    def split_emails(self, email_list, email_reminds=False, update=False):
        list_mail = re.split(r';|,', email_list)
        for email in list_mail:
            if len(email) != 0:
                if not email_reminds:
                    self.env['mncei.mail.reminder'].create(self.prepare_data_emails(email))
                elif email_reminds:
                    if any(email == email_id.email for email_id in self.email_remind_ids):
                        continue
                    else:
                        self.env['mncei.mail.reminder'].create(self.prepare_data_emails(email))
        if email_reminds and update:
            for email_id in email_reminds:
                if email_id.email not in list_mail:
                    email_id.write({'document_id': False})

    @api.onchange('email_reminder')
    def split_email_reminder(self):
        if self.email_reminder:
            list_mail = re.split(r';|,', self.email_reminder)
            for email in list_mail:
                if len(email) != 0:
                    if not self.email_remind_ids:
                        self.env['mncei.mail.reminder'].create(self.prepare_data_emails(email))
                    elif self.email_remind_ids:
                        if any(email == email_id.email for email_id in self.email_remind_ids):
                            continue
                        else:
                            self.env['mncei.mail.reminder'].create(self.prepare_data_emails(email))
            for email_id in self.email_remind_ids:
                if email_id.email not in list_mail:
                    self.email_remind_ids = [(3, email_id.id)]

    def name_get(self):
        result = []
        for legal in self:
            name = legal.document_number
            result.append((legal.id, name))
        return result

    @api.onchange('expired_date', 'reminder_date')
    def check_exp_date(self):
        if self.expired_date and self.reminder_date:
            if self.expired_date < self.reminder_date:
                return {'warning': {'title': _('Warning'), 'message': _("Tanggal Exp tidak boleh kurang dari tanggal reminder")}}
            elif self.periods_times_ids:
                for period_time in self.periods_times_ids:
                    period_time.unlink()

    # Method ketika saat di list view create split emails
    @api.model
    def create(self, vals):
        res = super(MnceiBaseDokumen, self).create(vals)
        if not vals.get('email_remind_ids') and vals.get('email_reminder'):
            res.split_emails(vals.get('email_reminder'))
        return res

    def write(self, vals):
        res = super(MnceiBaseDokumen, self).write(vals)
        if vals.get('email_reminder'):
            if self.email_remind_ids:
                self.split_emails(vals.get('email_reminder'), self.email_remind_ids, True)
            else:
                self.split_emails(vals.get('email_reminder'), update=True)
        return res

    # Check record yang sudah melewati tanggal expired
    @api.model
    def check_expire_document(self):
        legal_docs = self.env['mncei.doc'].search([('expired_date', '<=', fields.Date.today())])
        exp_state = self.env['mncei.doc.status'].search(['|', ('document_status', 'ilike', 'close'), ('document_status', 'ilike', 'expire')], limit=1)
        for legal_id in legal_docs:
            legal_id.write({'document_status': exp_state.id})

    # Membuat date reminder berdasarkan periode yang dipilih
    # Daily, Weekly, Monthly
    @api.model
    def check_date_reminder(self):
        legal_docs = self.env['mncei.doc'].search([('active', '=', True), ('reminder_date', '<=', fields.Date.today()), ('expired_date', '>=', fields.Date.today())])
        for legal in legal_docs:
            date_range = 0
            period_time = 1
            # Check Periode
            if not legal.periods_times_ids:
                if legal.periode_reminder and legal.expired_date and legal.reminder_date:
                    if 'Daily' in legal.periode_reminder.periode_reminder or 'daily' in legal.periode_reminder.periode_reminder:
                        date_range = (legal.expired_date - legal.reminder_date).days
                    if 'weekly' in legal.periode_reminder.periode_reminder or 'Week' in legal.periode_reminder.periode_reminder:
                        date_range = (legal.expired_date - legal.reminder_date).days // 7
                        period_time = 7
                    if 'monthly' in legal.periode_reminder.periode_reminder or 'Month' in legal.periode_reminder.periode_reminder:
                        date_range = (legal.expired_date - legal.reminder_date).days // 30
                        period_time = 30
                    # to create range date
                    if date_range <= 0:
                        date_range = 1

                    periods = legal.auto_create_date_reminder(date_range, period_time)
                    if periods:
                        mail_template = self.env.ref('mnc_document.email_template_email_reminder')
                        for period in periods:
                            legal.env['mncei.periode.reminder'].create(legal.prepare_date_reminder(period))
                            if period == fields.Date.today():
                                for email_id in legal.email_remind_ids:
                                    mail_template.send_mail(email_id.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': email_id.email})
            else:
                for periode_range in legal.periods_times_ids.filtered(lambda x: x.date_reminder == fields.Date.today()):
                    mail_template = self.env.ref('mnc_document.email_template_email_reminder')
                    for email_id in legal.email_remind_ids:
                        mail_template.send_mail(email_id.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': email_id.email})
                        periode_range.update({'is_done': True})


    # Pembuatan list tanggal untuk reminder berdasarkan periode yang dipilih
    def auto_create_date_reminder(self, date_range, period_time):
        date_list = []
        if date_range > 1:
            i = 1
            while i < date_range:
                if date_list:
                    count_date = date_list[-1] + timedelta(days=period_time)
                    if count_date < self.expired_date:
                        date_list.append(count_date)
                else:
                    count_date = self.reminder_date + timedelta(days=period_time)
                    if count_date < self.expired_date:
                        date_list.append(count_date)
                i += 1
        date_list.append(self.expired_date)
        date_list.append(self.reminder_date)
        return date_list

    # Prepare Data Record
    # Prepare data untuk pembuatan list tanggal
    def prepare_date_reminder(self, date_remain):
        return {
            'date_reminder': date_remain,
            'document_id': self.id
        }

    def prepare_data_emails(self, email):
        return {
            'email': email,
            'document_id': self.id
        }


# Category Document
class MnceiDocCateg(models.Model):
    _name = "mncei.doc.categ"
    _description = "Legal Dokumen Category"
    _order = "sequence, id"

    type_document = fields.Selection([
        ('perjanjian', 'Perjanjian'),
        ('perizinan', 'Perizinan')
    ], default='perjanjian', required=True, store=True, string='Document Type', tracking=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.", store=True)
    id_category = fields.Integer(related='id', store=True)
    document_category = fields.Char("Dokumen Category", size=150)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)
    legal_doc_ids = fields.One2many(
        'mncei.doc',
        'document_category',
        string='Legal Document', store=True
    )
    count_doc = fields.Integer(
        string='Total Document', compute='_get_document', store=True
    )

    @api.depends('legal_doc_ids')
    def _get_document(self):
        for status in self:
            total = 0
            if status.legal_doc_ids:
                total = len(status.legal_doc_ids.ids)
            status.count_doc = total

    def name_get(self):
        result = []
        for category in self:
            name = category.document_category
            result.append((category.id, name))
        return result


# Periods Document
class MnceiDocPeriod(models.Model):
    _name = "mncei.doc.period"
    _description = "Legal Dokumen Period"
    _order = "sequence, id"

    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.", store=True)
    id_periode = fields.Integer(related='id', store=True)
    periode_reminder = fields.Char("Period Reminder", size=45)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    def name_get(self):
        result = []
        for period in self:
            name = period.periode_reminder
            result.append((period.id, name))
        return result


# Status Document
class MnceiDocStatus(models.Model):
    _name = "mncei.doc.status"
    _description = "Legal Dokumen State"
    _order = "sequence, id"

    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.", store=True)
    id_status = fields.Integer(related='id', store=True)
    document_status = fields.Char("Document Status", size=45)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)
    legal_doc_ids = fields.One2many(
        'mncei.doc',
        'document_status',
        string='Legal Document', store=True
    )
    count_doc = fields.Integer(
        string='Total Document', compute='_get_document', store=True
    )
    is_dokumen = fields.Boolean(
        string='Perjanjian/Perizinan', store=True
    )
    is_lahan = fields.Boolean(
        string='Lahan', store=True
    )
    is_akta = fields.Boolean(
        string='Akta', store=True
    )
    is_surat = fields.Boolean(
        string='Surat', store=True
    )
    is_lap_wajib = fields.Boolean(
        string='Laporan Wajib', store=True
    )

    @api.depends('legal_doc_ids')
    def _get_document(self):
        for status in self:
            total = 0
            if status.legal_doc_ids:
                total = len(status.legal_doc_ids.ids)
            status.count_doc = total

    def name_get(self):
        result = []
        for status in self:
            name = status.document_status
            result.append((status.id, name))
        return result


class MnceiHardcopyLoc(models.Model):
    _name = "mncei.hardcopy.loc"
    _description = "Dokumen Hardcopy Location"
    _rec_name = 'hardcopy_location'
    _order = "sequence, id"

    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.", store=True)
    id_hardcopy_loc = fields.Integer(related='id', store=True)
    hardcopy_location = fields.Char("Hardcopy Location ", size=45)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    def name_get(self):
        result = []
        for hardloc in self:
            name = hardloc.hardcopy_location
            result.append((hardloc.id, name))
        return result


class TrackingDocument(models.Model):
    _name = "mncei.tracking"
    _description = "Tracking Document"

    parent_doc_id = fields.Many2one('mncei.doc', 'Document', store=True, ondelete='cascade')
    document_id = fields.Many2one('mncei.doc', 'Document', store=True, required=True, ondelete='cascade')
    description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('berlaku_sebagian', 'Berlaku Sebagian'),
        ('dicabut', 'Dicabut'),
    ], store=True, required=True)


class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    _order = "line_type_id, date_start desc, date_end desc"

    parent_doc_id = fields.Many2one('mncei.doc', 'Document', store=True, ondelete='cascade')
    document_id = fields.Many2one('mncei.doc', 'Document', store=True, required=True, ondelete='cascade')
    document_number = fields.Char("Document Number", related='document_id.document_number', store=True)
    # Status Tracking:
    # 1. Berlaku
    # 2. Berlaku Sebagian
    # 3. Dicabut
    # 4. Diubah
    # 5. Expired
    state = fields.Selection([
        ('berlaku', 'Berlaku'),
        ('berlaku_sebagian', 'Berlaku Sebagian'),
        ('dicabut', 'Dicabut'),
        ('diubah', 'Diubah'),
        ('expired', 'Expired'),
    ], store=True)
    state_desc = fields.Char('States', compute='_get_state', store=True)

    @api.depends('state')
    def _get_state(self):
        for line in self:
            resume_line_obj = self.env['hr.resume.line']
            state = dict(resume_line_obj._fields['state'].selection).get(line.state) or ""
            line.state_desc = f"[{state}]"
