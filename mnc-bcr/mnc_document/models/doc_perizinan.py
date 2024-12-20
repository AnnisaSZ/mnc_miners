from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging
import re


_logger = logging.getLogger(__name__)


class MnceiBasePerizinan(models.Model):
    _name = "mncei.perizinan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Perizinan"
    _order = 'id desc'

    # Information
    parties = fields.Char("The Parties", size=50, store=True, required=True)
    category = fields.Selection([
        ('Baru', 'Baru'),
        ('Perpanjangan', 'Perpanjangan')
    ], default='Baru', store=True, required=True, string='Category')
    license_number = fields.Char("License Number", size=25, store=True, required=True)
    license_name = fields.Char("License Name", size=30, store=True, required=True)
    license_date = fields.Date("License Date", store=True, required=True)
    licensor = fields.Char("Licensor", size=50, store=True, required=True)
    license_obligation = fields.Text("License Obligation", size=225, store=True, help="Penjelasan tentang dokumen")
    company = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id, store=True, required=True)
    document_type = fields.Selection([
        ('original', 'Original'),
        ('digital', 'Digital')
    ], default='original', store=True, required=True, string='Document Type')
    location_doc_id = fields.Many2one('mncei.hardcopy.loc', store=True, required=True, size=250)
    rak = fields.Selection([
        ('Rak_1', 'Rak 1'),
        ('Rak_2', 'Rak 2'),
        ('Rak_3', 'Rak 3'),
        ('Rak_4', 'Rak 4'),
        ('Rak_5', 'Rak 5')
    ], default='Rak_1', required=True, store=True, string='Partition', tracking=True)
    url_penyimpanan = fields.Text('URL Location', default='/', store=True, size=150)

    pic = fields.Many2one('res.users', 'PIC', default=lambda self: self.env.user, store=True, required=True, copy=False)
    pic_phone = fields.Char("Phone", size=16, store=True, required=True, help="Nomor telepon penanggung jawab dokumen")

    # Information Date
    release_date = fields.Date("License Date", store=True, required=True, help="Tanggal dokumen terbit")
    expired_date = fields.Date("License End Date", store=True, required=True, help="Tanggal masa berlaku dokumen")
    reminder_date = fields.Date("Reminder Date", store=True, required=True, help="Tanggal mulai mengirimkan dokumen")

    # Reminder
    periode_reminder = fields.Many2one('mncei.doc.period', 'Periode', store=True, required=True, domain="[('state', '=', 'active')]", ondelete='cascade')
    document_status = fields.Many2one('mncei.doc.status', 'Status', tracking=True, store=True, required=True, domain="[('state', '=', 'active'), ('is_dokumen', '=', True)]")
    email_reminder = fields.Char("Email Reminder", size=150, store=True)
    email_remind_ids = fields.One2many('mncei.mail.reminder', 'perizinan_id', string="Emails", store=True, copy=False)

    periods_times_ids = fields.One2many('mncei.periode.reminder', 'perizinan_id', string="Periode Time", store=True, copy=False)

    # Parameter
    # is_netral = fields.Boolean('Netral', compute='check_state', store=True)
    # is_process = fields.Boolean('Process', compute='check_state', store=True)
    # is_release = fields.Boolean('Release', compute='check_state', store=True)

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
            'default_perizinan_id': self.id
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
                    email_id.write({'perizinan_id': False})

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
            name = legal.license_number
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
        res = super(MnceiBasePerizinan, self).create(vals)
        if not vals.get('email_remind_ids') and vals.get('email_reminder'):
            res.split_emails(vals.get('email_reminder'))
        return res

    def write(self, vals):
        res = super(MnceiBasePerizinan, self).write(vals)
        if vals.get('email_reminder'):
            if self.email_remind_ids:
                self.split_emails(vals.get('email_reminder'), self.email_remind_ids, True)
            else:
                self.split_emails(vals.get('email_reminder'), update=True)
        return res

    # Check record yang sudah melewati tanggal expired
    @api.model
    def check_expire_document(self):
        legal_docs = self.env['mncei.perizinan'].search([('expired_date', '<=', fields.Date.today())])
        exp_state = self.env['mncei.doc.status'].search(['|', ('document_status', 'ilike', 'close'), ('document_status', 'ilike', 'expire')], limit=1)
        for legal_id in legal_docs:
            legal_id.write({'document_status': exp_state.id})

    # Membuat date reminder berdasarkan periode yang dipilih
    # Daily, Weekly, Monthly
    @api.model
    def check_date_reminder(self):
        legal_docs = self.env['mncei.perizinan'].search([('reminder_date', '<=', fields.Date.today()), ('expired_date', '>=', fields.Date.today())])
        print("Data Legal")
        print(legal_docs)
        print(fields.Date.today())
        for legal in legal_docs:
            date_range = 0
            period_time = 1
            # Check Periode
            mail_template = self.env.ref('mnc_document.email_template_perizinan')
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
                        # mail_template = self.env.ref('mnc_document.email_template_perizinan')
                        for period in periods:
                            legal.env['mncei.periode.reminder'].create(legal.prepare_date_reminder(period))
                            if period == fields.Date.today():
                                for email_id in legal.email_remind_ids:
                                    mail_template.send_mail(email_id.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': email_id.email})
            else:
                for periode_range in legal.periods_times_ids.filtered(lambda x: x.date_reminder == fields.Date.today()):
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
            'perizinan_id': self.id
        }

    def prepare_data_emails(self, email):
        return {
            'email': email,
            'perizinan_id': self.id
        }
