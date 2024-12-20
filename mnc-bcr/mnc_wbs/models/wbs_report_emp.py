from odoo import fields, models, api, _
from odoo.exceptions import ValidationError



class WBSReportEmp(models.Model):
    _name = 'wbs.report.emp'
    _order = 'id desc'

    is_from_head = fields.Boolean('From Head Auditor', store=True)
    from_head = fields.Boolean(string='From Head Auditor')
    is_head = fields.Boolean(string='From Head Auditor', compute="check_is_head")
    is_dir = fields.Boolean(string='From Director', compute="check_is_dir")
    is_employee = fields.Boolean(string='is_employee', compute="check_is_employee")

    state = fields.Selection([
        ('process', 'New'),
        ('assigned', 'Assigned'),
        ('process_audit', 'Process'),
        ('report_audit', 'Report Audit'),
        ('result_audit', 'Result Audit'),
        ('close', 'Closed'),
        ('cancel', 'Canceled'),
    ], string='Status', default='assigned', store=True, required=True, copy=False, track_visibility='onchange')

    # Reporting User 
    username = fields.Char('Full Name', related="list_report_id.user_name", readonly=True)
    userphone = fields.Char('Phone Number', related="list_report_id.user_phone", readonly=True)
    usercompany = fields.Char('Company', related="list_report_id.user_company")
    useremail = fields.Char('Email', related="list_report_id.user_email", readonly=True)

    # Reported Case
    list_report_id = fields.Many2one('wbs.report', string='Report Title', store=True,copy=False, readonly=True)
    name = fields.Char('Report Number', default="New", store=True, readonly=True)
    title = fields.Char('Report Title', default="New", store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Business Unit', store=True,copy=False, readonly=True)
    start_date = fields.Date('Start Date', store=True, readonly=True)
    end_date = fields.Date('End Date', store=True, readonly=True)
    casedescription = fields.Text('Description', related="list_report_id.description", readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', copy=False, readonly=True)

    # Director
    list_dir_report_id = fields.Many2one('wbs.report.bod', string='Report Director', store=True,copy=False)
    director_id = fields.Many2one('mncei.employee', copy=False, string='Director Name', readonly=True)
    dir_notes = fields.Text('Director Notes')
    start_date_audit = fields.Date('Start Date Audit', store=True, readonly=True)
    end_date_audit = fields.Date('End Date Audit', store=True, readonly=True)
    dir_attachment_ids = fields.One2many('wbs.report.bod.attach', 'emp_id', copy=False, readonly=True)

    # Head Auditor
    list_head_report_id = fields.Many2one('wbs.report.head', string='Report Head Auditor', store=True, copy=False, ondelete='cascade')
    head_auditor_id = fields.Many2one('mncei.employee', copy=False, string='Head Auditor', readonly=True)
    head_auditor_notes = fields.Text('Head Auditor Notes', readonly=True)
    head_auditor_attachment_ids = fields.One2many('wbs.report.head.attach', 'emp_id', copy=False)

    # Employee
    employee_id = fields.Many2one('mncei.employee', copy=False, string="Assign To", readonly=True)
    user_employee_id = fields.Many2one('res.users', copy=False, string="User Employee", compute='_get_user_employee', store=True)
    jabatan_emp = fields.Many2one('mncei.jabatan', related='employee_id.jabatan',string="Jabatan", copy=False)
    result_auditor_emp = fields.Text(string="Employee Notes", copy=False)
    emp_attachment_ids = fields.One2many('wbs.report.emp.attach', 'emp_id', copy=False)
    member_ids = fields.Many2many('mncei.employee', string='Members')

    @api.onchange('emp_attachment_ids')
    def _check_emp_attachment_ids(self):
        for record in self:
            if len(record.emp_attachment_ids) > 15:
                raise ValidationError('You reached maximum attachments. Your maximal attachment is 15 files.')

    @api.depends('employee_id')
    def _get_user_employee(self):
        for wbs_employee in self:
            wbs_employee.user_employee_id = False
            user = self.env['res.users'].search([('mncei_employee_id', '=', wbs_employee.employee_id.id)], limit=1)
            if user:
                wbs_employee.user_employee_id = user

    def button_close(self):
        self.state = 'close'
        return

    def button_cancel(self):
        self.state = 'cancel'
        return

    def button_report_audit(self):
        self.state = 'report_audit'
        if self.list_head_report_id:
            self.list_head_report_id.state = 'report_audit'
            head_auditor = self.head_auditor_id

            # To Send
            template_id = self.env.ref('mnc_wbs.notification_complete_report_auditor_mail_template')
            template = template_id.with_context(dbname=self._cr.dbname, invited_users=head_auditor)
            template.sudo().send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': head_auditor.email})
        else:
            self.list_dir_report_id.state = 'report_audit'
        return

    def button_revise_audit(self):
        self.state = 'process_audit'
        self.list_head_report_id.state = 'process_audit'
        self.list_dir_report_id.state = 'process_audit'
        employee_id = self.employee_id

        # To Send
        template_id = self.env.ref('mnc_wbs.notification_revise_by_bod_mail_template')
        template = template_id.with_context(dbname=self._cr.dbname, invited_users=employee_id)
        template.sudo().send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': employee_id.email})

    @api.depends('dir_notes')
    def change_dir_notes(self):
        for rec in self:
            rec.list_dir_report_id.director_notes = self.dir_notes 
        return

    def open_report(self, context=None):
        if not self.from_head:
            res = self.list_head_report_id.prepare_employee_value(self.list_head_report_id.employee_id)
            self.update(res)
            attch_ids = []
            Attachment = self.env['ir.attachment']
            for files in self.list_head_report_id.attachment_ids:
                if files and files.name != '':
                    attachment_id = Attachment.create({
                        'name': files.name,
                        'type': 'binary',
                        'datas': files.datas,
                        'res_model': 'wbs.report.emp',
                        'res_id': self.id
                    })
                    attch_ids.append(attachment_id.id)
            self.update({
                'attachment_ids': [(6, 0, attch_ids)],
            })

            for file in self.list_head_report_id.dir_attachment_ids:
                file.update({'emp_id': self.id})

        return {
            'name': _("Auditor Report"),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wbs.report.emp',
            'res_id': self.id,
        }

    def check_is_head(self):
        for record in self:
            if record.head_auditor_id == self.env.user.mncei_employee_id:
                record.is_head = True
            else:
                record.is_head = False

    def check_is_dir(self):
        for record in self:
            if record.director_id == self.env.user.mncei_employee_id:
                record.is_dir = True
            else:
                record.is_dir = False

    def check_is_employee(self):
        for record in self:
            if record.employee_id == self.env.user.mncei_employee_id:
                record.is_employee = True
            else:
                record.is_employee = False


    def open_from_head(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Result From Employee',
            'view_mode': 'form',
            'res_model': 'wbs.report.emp',
            'view_id': self.env.ref('mnc_wbs.list_report_emp_view_form').id,
            'res_id': self.id,
            'target': 'new',
            'context': {
                'form_view_initial_mode': 'edit',
                'create': '0',
                'delete': '0',
            },
        }

    def open_form_attach(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'List Attachment Head Auditor',
            'view_mode': 'form',
            'res_model': 'wbs.report.emp',
            'view_id': self.env.ref('mnc_wbs.attachment_from_head_form').id,
            'res_id': self.id,
            'target': 'new',
            'context': {
                'form_view_initial_mode': 'edit',
                'create': '0',
                'delete': '0',
            },
        }
    
class WBSReportEmpAttachment(models.Model):
    _name = "wbs.report.emp.attach"
    _order = 'id desc'


    dir_id = fields.Many2one('wbs.report.bod', store=True, copy=False)
    emp_id = fields.Many2one('wbs.report.emp', store=True, copy=False)
    head_id = fields.Many2one('wbs.report.head', store=True, copy=False)

    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True
    )
    part_filename = fields.Char(
        string='Filename Part', store=True
    )
