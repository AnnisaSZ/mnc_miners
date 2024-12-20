from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime, date

ROMAN_NUMBER = {
    '1': 'I',
    '2': 'II',
    '3': 'III',
    '4': 'IV',
    '5': 'V',
    '6': 'VI',
    '7': 'VII',
    '8': 'VIII',
    '9': 'IX',
    '10': 'X',
    '11': 'XI',
    '12': 'XII',
}

class ITSubsForm(models.Model):
    _name = 'it.subs.form'
    _description = 'IT Subscription Form'
    _order = 'id desc'

    def _get_sequence(self):
        sequence = self.env['ir.sequence'].sudo().next_by_code('it.subs.form')
        code_month = ROMAN_NUMBER[str(datetime.now().month)]
        sequence = sequence.replace('CUSTOMCODE', code_month)
        return sequence or '/'
   
    name = fields.Char('ID Subcription', store=True, required=True, copy=False, default="New")
    classification = fields.Selection([
        ('software', 'Software'),
        ('hardware', 'Hardware'),
     ], string='Classification', default='software', required=True, store=True, copy=False)
    subs_type_id = fields.Many2one('master.type.itsubs', string='Subscription Type', store=True, required=True, copy=False)
    project_name = fields.Char('Project Name', store=True, required=True, copy=False)
    vendor_id = fields.Many2one('master.vendor.itsubs', string='Vendor', store=True, required=True, copy=False)
    agreement_date = fields.Date('First Agreement Date', store=True, required=True, copy=False)
    remark = fields.Char('Remarks', store=True, copy=False)
    company_id = fields.Many2one('res.company', string='Bisnis Unit', store=True, required=True, ondelete='cascade')
    pic_id = fields.Many2one('mncei.employee', string="PIC Name", default=False, required=True, ondelete='cascade', index=True, store=True)
    pic_no = fields.Char('PIC Number', store=True, required=False, copy=False, related="pic_id.no_wa")
    hard_file_id = fields.Many2one('master.location.itsubs', string='Hard File Location', store=True, required=True, copy=False)
    detail_loc = fields.Char('Detail Location', store=True, required=True, copy=False)
    soft_file_id = fields.Char('Soft File Location', store=True, required=True, copy=False)
    attachment = fields.Binary('Attachments', attachment=True)
    filename_attachment = fields.Char('Name Attachments', store=True)

    renewal_reminder_ids = fields.One2many('it.subs.form.line', 'form_id', string='Renewal Reminder List')

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        for form in self:
            if form.vendor_id:
                form.agreement_date = form.vendor_id.first_agreement
            else:
                form.agreement_date = False


    @api.constrains('attachment')
    def check_attachment(self):
        for form in self:
            if form.attachment:
                tmp = form.filename_attachment.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF', 'png', 'PNG'):
                    raise ValidationError(_("The file must be a PDF/PNG format file"))

    def check_reminder(self):
         for form in self:
            today = fields.Date.today()
            line = form.renewal_reminder_ids[-1]
            if line.end_date >= today:
                line.send_notif_reminder()
                return
            
    @api.model
    def create(self, vals):
        res = super(ITSubsForm, self).create(vals)
        seq = self._get_sequence()
        res.update({"name": seq})
        return res
            
            
class ITSubsFormLine(models.Model):
    _name = 'it.subs.form.line'
    _description = 'IT Subscription Line'
    _order = 'id'

    form_id = fields.Many2one('it.subs.form', string='Form ID')
    name = fields.Char('Name', store=True, required=False, copy=False, related='form_id.name')
    start_date = fields.Date('Start Date', store=True, required=True, copy=False)
    end_date = fields.Date('End Date', store=True, required=True, copy=False)
    period_subs = fields.Selection([
        ('weeks', 'Weekly'),
        ('months', 'Monthly'),
        ('years', 'Yearly'),
    ], string='Period Subscription',  default='weeks', store=True, required=True, copy=False)
    status_id = fields.Many2one('master.status.itsubs', string='Status', store=True, required=True, copy=False)
    remark = fields.Char('Remarks', store=True, copy=False)
    attachment = fields.Binary('Attachments', attachment=True, required=False)
    filename_attachment = fields.Char('Name Attachments', store=True)
    reminder_to = fields.Char(string='Reminder To (Email)', required=True)
    reminder_type = fields.Selection([
        ('days', 'Daily'),
        ('weeks', 'Weekly'),
        ('months', 'Monthly'),
     ], string='Reminder Type', default='days', required=True, store=True, copy=False)
    start_reminder = fields.Date('Start Reminder', store=True, required=True, copy=False)
    unit = fields.Integer(string='Units', required=True)
    currency_id = fields.Many2one(related='form_id.vendor_id.currency_id', store=True, string='Currency', readonly=True)
    unit_price = fields.Monetary(string='Unit Price', required=True)
    total_price = fields.Monetary(string='Total Cost', compute='compute_total_price', store=True)

    @api.depends('unit', 'unit_price')
    def compute_total_price(self):
        for rec in self:
            if rec.unit and rec.unit_price:
                rec.total_price = rec.unit * rec.unit_price

    def get_cron_job(self):
        res = self.env['ir.cron'].search([('name', '=', 'Reminder IT Subs ' + self.form_id.name)])
        return res

    def create_cron_job(self):
        existing_cron = self.get_cron_job()
        interval_time = self.reminder_type
        interval_number = 1
        today = fields.Date.today()
        
        cron_vals = {
            'name': 'Reminder IT Subs ' + self.form_id.name,
            'model_id': self.env.ref('mnc_it_subs.model_it_subs_form_line').id,
            'state': 'code',
            'user_id': self.env.ref('base.user_admin').id,
            'interval_number': interval_number,
            'interval_type': interval_time,
            'numbercall': -1,
            'active': 1,
            'code': 'model.check_reminder()',
        }

        if today < self.start_reminder:
            cron_vals['nextcall'] = self.start_reminder
        if existing_cron:
            if today >= self.end_date:
                cron_vals['active'] = False
            cron_job = existing_cron.write(cron_vals)
        else:
            cron_vals['nextcall'] = self.start_reminder
            cron_job = self.env['ir.cron'].create(cron_vals)
        return cron_job
    
    def check_reminder(self):
        self = self.search([]).mapped('form_id')
        for line in self:
            line.check_reminder()

    @api.depends('start_reminder', 'end_date')
    def check_status_reminder(self):
        today = fields.Date.today()
        self = self.search([])
        for rec in self:
            rec.create_cron_job()
            if rec.start_reminder >= today and rec.end_date < today:
                rec.status_id = self.env['master.status.itsubs'].search([('name', '=', 'Due Date')])
            elif rec.end_date <= today:
                rec.status_id = self.env['master.status.itsubs'].search([('name', '=', 'Expired')])

    def send_notif_reminder(self):
        mail_template = self.env.ref('mnc_it_subs.notification_it_subs_mail_template')
        mail_template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': self.reminder_to})
        return
    
    @api.model
    def create(self, vals):
        res = super(ITSubsFormLine, self).create(vals)
        separator_string = ", "
        error_list = []
        if vals['unit'] <= 0 :
            error_list.append('Units')
        if vals['unit_price'] <= 0 :
            error_list.append('Unit Price')
        if not vals['filename_attachment']:
            error_list.append('Attachment')
        if error_list:
            raise ValidationError(_("You have to input the " + separator_string.join(error_list) + " before save!"))
        return res

    



    