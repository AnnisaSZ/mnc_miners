from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import html_translate


class WBSReportHead(models.Model):
    _name = 'wbs.report.head'
    _order = 'id desc'

    is_not_auditor = fields.Boolean('Not Auditor', default=False)
    state = fields.Selection([
        ('process', 'New'),
        ('assigned', 'Assigned'),
        ('process_audit', 'Process'),
        ('report_audit', 'Report Audit'),
        ('result_audit', 'Result'),
        ('close', 'Closed'),
        ('cancel', 'Canceled'),
    ], string='Status', default='process', store=True, required=True, copy=False, track_visibility='onchange')

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
    list_dir_report_id = fields.Many2one('wbs.report.bod', string='Report Director', store=True,copy=False, readonly=True, ondelete='cascade')
    director_id = fields.Many2one('mncei.employee', copy=False, string='Director Name', readonly=True)
    dir_notes = fields.Text('Director Notes')
    start_date_audit = fields.Date('Start Date Audit', store=True, readonly=True)
    end_date_audit = fields.Date('End Date Audit', store=True, readonly=True)
    dir_attachment_ids = fields.One2many('wbs.report.bod.attach', 'head_id', copy=False, readonly=True)
    is_dir = fields.Boolean(string='From Director', compute="check_is_dir")

    # Head Audit
    employee_id = fields.Many2one('mncei.employee', copy=False, string="Assign To")
    head_auditor_id = fields.Many2one('mncei.employee', copy=False, string="Full Name")
    user_head_employee_id = fields.Many2one('res.users', copy=False, string="User Employee", compute='_get_user_employee', store=True)
    master_head_auditor_id = fields.Many2one('wbs.auditor', copy=False, string="Full Name", readonly=True)
    head_auditor_notes = fields.Text('Head Auditor\'s Notes')
    head_attachment_ids = fields.One2many('wbs.report.head.attach', 'head_id', copy=False)
    result_attachment_ids = fields.One2many('wbs.report.head.attach', 'result_head_id', copy=False)
    report_as = fields.Selection([
        ('own', 'Yourself'),
        ('single', 'Single'),
        ('group', 'Group'),
    ], string='Report As', default='own', store=True, required=True, copy=False, tracking=True)

    # Assign Auditor
    list_emp_report_ids = fields.One2many('wbs.report.emp', 'list_head_report_id', string='Report Employee', copy=False)
    member_ids = fields.Many2many('mncei.employee', string='Members')
    # Summary
    summary_audit = fields.Html('Tip description', translate=html_translate)
    is_summary = fields.Boolean('Is Summary', store=True, default=False)

    @api.depends('head_auditor_id')
    def _get_user_employee(self):
        for wbs_head in self:
            wbs_head.user_head_employee_id = False
            user = self.env['res.users'].search([('mncei_employee_id', '=', wbs_head.head_auditor_id.id)], limit=1)
            if user:
                wbs_head.user_head_employee_id = user

    def check_is_dir(self):
        for record in self:
            if record.director_id == self.env.user.mncei_employee_id:
                record.is_dir = True
            else:
                record.is_dir = False

    @api.onchange('head_attachment_ids')
    def _check_head_attachment_ids(self):
        for record in self:
            if len(record.head_attachment_ids) > 15:
                raise ValidationError('You reached maximum attachments. Your maximal attachment is 15 files.')

    @api.onchange('employee_ids')
    def _check_employee_ids(self):
        for record in self:
            if len(record.employee_ids) > 2:
                raise ValidationError('Not more than 2 Auditors')

    def assign_to_employee(self):
        if not self.is_not_auditor:
            for employee in self.list_emp_report_ids:
                res = self.prepare_employee_value()
                attch_ids = []
                Attachment = self.env['ir.attachment']
                for files in self.attachment_ids:
                    if files and files.name != '':
                        attachment_id = Attachment.create({
                            'name': files.name,
                            'type': 'binary',
                            'datas': files.datas,
                            'res_model': 'wbs.report.emp',
                            'res_id': employee.id
                        })
                        attch_ids.append(attachment_id.id)
                employee.update({
                    'attachment_ids': [(6, 0, attch_ids)],
                })

                for file in self.dir_attachment_ids:
                    file.update({'emp_id': employee.id})
                employee.write(res)

            template_id = self.env.ref('mnc_wbs.notification_to_auditor_report_mail_template')
            # To Send
            template = template_id.with_context(dbname=self._cr.dbname, invited_users=employee.employee_id)
            template.sudo().send_mail(employee.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': employee.employee_id.email})

        self.write({'state': 'process_audit'})
        self.list_dir_report_id.change_state_to_process()
        return True

    def prepare_employee_value(self):
        vals = ({
            'director_id': self.director_id.id,
            'head_auditor_id': self.head_auditor_id.id,
            'is_from_head': True,
            'state': 'process_audit',
            'list_report_id': self.list_report_id.id,
            'list_dir_report_id': self.list_dir_report_id.id,
            'name': self.name,
            'title': self.title,
            'company_id': self.company_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'dir_notes': self.dir_notes,
            'start_date_audit': self.start_date_audit,
            'end_date_audit': self.end_date_audit,
            'from_head': True,
        })
        return vals
    
    @api.depends('head_auditor_notes')
    def check_head_auditor_notes(self):
        for rec in self:
            rec.summary_audit = rec.head_auditor_notes

    def director_closing(self):
        for record in self:
            record.button_close()
            if not record.list_dir_report_id.list_auditor_report_ids.filtered(lambda line: line.state != 'close'):
                record.list_dir_report_id.button_close()
        return

    def button_close(self):
        self.state = 'close'
        for employee in self.list_emp_report_ids:
            employee.button_close()
        return

    def button_cancel(self):
        self.state = 'cancel'
        for employee in self.list_emp_report_ids:
            employee.button_cancel()
        return

    def open_head_from_dir(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Result From Head Auditor',
            'view_mode': 'form',
            'res_model': 'wbs.report.head',
            'view_id': self.env.ref('mnc_wbs.list_report_head_view_form').id,
            'res_id': self.id,
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit',
                'create': '0',
                'delete': '0',
            },
        }
        

    def result_to_director(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Result From Head Auditor',
            'view_mode': 'form',
            'res_model': 'wbs.report.head',
            'res_id': self.id,
            'view_id': self.env.ref('mnc_wbs.report_head_summary_form_view').id,
            'target': 'new',
            'context': {
                'form_view_initial_mode': 'edit',
                'create': '0',
                'delete': '0',
                'default_wbs_head_id': self.id,
                'default_head_auditor_notes': self.head_auditor_notes,
            },
        }
    
    def action_submit(self):
        if not self.head_auditor_notes:
            raise ValidationError(_("Please input your summary audit"))
        self.write({
            'summary_audit': self.head_auditor_notes,
            'is_summary': True,
            'state': 'result_audit',
        })
        if self.list_emp_report_ids:
            for report_emp in self.list_emp_report_ids:
                report_emp.write({'state': 'result_audit'})
        wbs_bod = self.list_dir_report_id
        wbs_bod.write({'state': 'result_audit'})

        director = self.director_id

        # To Send
        template_id = self.env.ref('mnc_wbs.notification_complete_report_headauditor_mail_template')
        template = template_id.with_context(dbname=self._cr.dbname, invited_users=director)
        template.sudo().send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': director.email})

        return True

    def button_revise_head_audit(self):
        state = 'process_audit'
        self.state = state
        self.is_summary = False
        self.list_dir_report_id.state = state
        for auditor in self.list_emp_report_ids:
            auditor.state = state
        employee_id = self.employee_id

        # To Send
        template_id = self.env.ref('mnc_wbs.notification_revise_by_bod_mail_template')
        template = template_id.with_context(dbname=self._cr.dbname, invited_users=employee_id)
        template.sudo().send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': employee_id.email})

    @api.onchange('list_emp_report_ids', 'list_emp_report_ids.employee_id', 'report_as')
    def _check_employee_id(self):
        for rec in self:
            master_audit = self.env['wbs.auditor'].search([('head_audit_id', '=', rec.head_auditor_id.id)])
            member = master_audit.auditor_1_ids.ids + master_audit.auditor_2_ids.ids + master_audit.auditor_3_ids.ids
            rec.member_ids = member
            auditor_1_temp = master_audit.auditor_1_ids.ids
            auditor_3_temp = master_audit.auditor_3_ids.ids
            for employee in rec.list_emp_report_ids.employee_id:
                if employee:
                    auditor_1 = self.master_head_auditor_id.filtered(lambda x: employee.id in x.auditor_1_ids.ids)
                    auditor_2 = self.master_head_auditor_id.filtered(lambda x: employee.id in x.auditor_2_ids.ids)
                    auditor_3 = self.master_head_auditor_id.filtered(lambda x: employee.id in x.auditor_3_ids.ids)
                    if auditor_1:
                        rec.member_ids = [(3, employee.id)]
                        auditor_1_temp = list(set(auditor_1_temp) - set(employee.ids))
                        rec.member_ids = [(6, 0, auditor_1_temp)]
                    if auditor_1 or auditor_2:
                        rec.member_ids = [(6, 0, auditor_3_temp)]
            if self.report_as == 'single':
                rec.member_ids = [(6, 0, auditor_1_temp)]

    def write(self, vals):
        res = super(WBSReportHead, self).write(vals)
        if vals.get('list_emp_report_ids'):
            if self.state == 'assigned' and len(self.list_emp_report_ids.ids) >= 0 and self.report_as != 'own':
                self.assign_to_employee()
                self.state = 'process_audit'
        return res


class WBSReportHeadAttachment(models.Model):
    _name = "wbs.report.head.attach"
    _order = 'id desc'

    dir_id = fields.Many2one('wbs.report.bod', store=True, copy=False)
    emp_id = fields.Many2one('wbs.report.emp', store=True, copy=False)
    head_id = fields.Many2one('wbs.report.head', store=True, copy=False)
    result_head_id = fields.Many2one('wbs.report.head', store=True, copy=False)
     

    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True, store=True
    )
    part_filename = fields.Char(
        string='Filename Part', store=True, readonly=True
    )
