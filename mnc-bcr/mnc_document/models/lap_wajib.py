from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging
import re


_logger = logging.getLogger(__name__)


class MnceiBaseLaporanWajib(models.Model):
    _name = "mncei.lap.wajib"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Laporan Wajib"
    _order = 'id desc'

    doc_name = fields.Char('Document Name', store=True, size=30, required=True)
    doc_number = fields.Char('Document Number', store=True, size=25, required=True)
    doc_date = fields.Date('Document Date', store=True, required=True)
    company = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id, store=True, required=True)
    description = fields.Text('Description', store=True, required=True, size=700)
    location_doc_id = fields.Many2one('mncei.hardcopy.loc', store=True, required=True, size=250)
    rak = fields.Selection([
        ('Rak_1', 'Rak 1'),
        ('Rak_2', 'Rak 2'),
        ('Rak_3', 'Rak 3'),
        ('Rak_4', 'Rak 4'),
        ('Rak_5', 'Rak 5')
    ], default='Rak_1', required=True, store=True, string='Partition', tracking=True)
    url_penyimpanan = fields.Text('URL Location', defaul="/", store=True, size=150)

    periode_reminder = fields.Many2one('mncei.doc.period', 'Periode', store=True, required=True, domain="[('state', '=', 'active')]", ondelete='cascade')
    document_status = fields.Many2one('mncei.doc.status', 'Status', tracking=True, store=True, required=True, domain="[('state', '=', 'active'), ('is_lap_wajib', '=', True)]")
    instansi = fields.Char('Instansi Terkait', store=True, size=50)
    upload_doc = fields.Binary(
        string='Upload Document', store=True, attachment=True
    )

    # id_document = fields.Integer(default=1, string='Document', store=True)
    reminder_date = fields.Date("Reminder Start", store=True, required=True, help="Tanggal mulai mengirimkan dokumen")
    reminder_finish = fields.Date("Reminder Finish", store=True, required=True, help="Tanggal berakhir mengirimkan dokumen")

    email_reminder = fields.Char("Email Reminder", size=150, store=True)
    email_remind_ids = fields.One2many('mncei.mail.reminder', 'perizinan_id', string="Emails", store=True, copy=False)
    periods_times_ids = fields.One2many('mncei.periode.reminder', 'laporan_id', string="Periode Time", store=True, copy=False)
    email_remind_ids = fields.One2many('mncei.mail.reminder', 'laporan_id', string="Emails", store=True, copy=False)

    def add_email(self):
        self.ensure_one()
        context = {
            'default_laporan_id': self.id
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
            name = legal.doc_number
            result.append((legal.id, name))
        return result

    @api.onchange('reminder_finish', 'reminder_date')
    def check_exp_date(self):
        if self.reminder_finish and self.reminder_date:
            if self.reminder_finish < self.reminder_date:
                return {'warning': {'title': _('Warning'), 'message': _("Tanggal Reminder Finish tidak boleh kurang dari tanggal Reminder Start")}}
            elif self.periods_times_ids:
                for period_time in self.periods_times_ids:
                    period_time.unlink()

    # Method ketika saat di list view create split emails
    @api.model
    def create(self, vals):
        res = super(MnceiBaseLaporanWajib, self).create(vals)
        if not vals.get('email_remind_ids') and vals.get('email_reminder'):
            res.split_emails(vals.get('email_reminder'))
        return res

    def write(self, vals):
        res = super(MnceiBaseLaporanWajib, self).write(vals)
        if vals.get('email_reminder'):
            if self.email_remind_ids:
                self.split_emails(vals.get('email_reminder'), self.email_remind_ids, True)
            else:
                self.split_emails(vals.get('email_reminder'), update=True)
        return res

    # Membuat date reminder berdasarkan periode yang dipilih
    # Daily, Weekly, Monthly
    @api.model
    def check_date_reminder(self):
        legal_docs = self.env['mncei.lap.wajib'].search([('reminder_date', '<=', fields.Date.today()), ('reminder_finish', '>=', fields.Date.today())])
        print("Data Legal")
        print(legal_docs)
        for legal in legal_docs:
            date_range = 0
            period_time = 1
            # Check Periode
            mail_template = self.env.ref('mnc_document.email_template_laporan')
            if not legal.periods_times_ids:
                if legal.periode_reminder and legal.reminder_finish and legal.reminder_date:
                    if 'Daily' in legal.periode_reminder.periode_reminder or 'daily' in legal.periode_reminder.periode_reminder:
                        date_range = (legal.reminder_finish - legal.reminder_date).days
                    if 'weekly' in legal.periode_reminder.periode_reminder or 'Week' in legal.periode_reminder.periode_reminder:
                        date_range = (legal.reminder_finish - legal.reminder_date).days // 7
                        period_time = 7
                    if 'monthly' in legal.periode_reminder.periode_reminder or 'Month' in legal.periode_reminder.periode_reminder:
                        date_range = (legal.reminder_finish - legal.reminder_date).days // 30
                        period_time = 30
                    # to create range date
                    if date_range <= 0:
                        date_range = 1

                    periods = legal.auto_create_date_reminder(date_range, period_time)
                    if periods:
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
                    if count_date < self.reminder_finish:
                        date_list.append(count_date)
                else:
                    count_date = self.reminder_date + timedelta(days=period_time)
                    if count_date < self.reminder_finish:
                        date_list.append(count_date)
                i += 1
        date_list.append(self.reminder_finish)
        date_list.append(self.reminder_date)
        return date_list

    # Prepare Data Record
    # Prepare data untuk pembuatan list tanggal
    def prepare_date_reminder(self, date_remain):
        return {
            'date_reminder': date_remain,
            'laporan_id': self.id
        }

    def prepare_data_emails(self, email):
        return {
            'email': email,
            'laporan_id': self.id
        }
