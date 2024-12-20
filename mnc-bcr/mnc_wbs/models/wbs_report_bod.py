from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class WBSReportBod(models.Model):
    _name = 'wbs.report.bod'
    _order = 'id desc'

    state = fields.Selection([
        ('process', 'New'),
        ('assigned', 'Assigned'),
        ('process_audit', 'Process Audit'),
        ('report_audit', 'Report Audit'),
        ('result_audit', 'Result Audit'),
        ('close', 'Closed'),
        ('cancel', 'Canceled'),
    ], string='Status', default='process', store=True, required=True, copy=False, track_visibility='onchange')

    # Profile User
    list_report_id = fields.Many2one('wbs.report', string='Review By Director', store=True,copy=False, readonly=True)
    user_name = fields.Char(related="list_report_id.create_uid.name", string="Full Name")
    user_phone = fields.Char(related="list_report_id.create_uid.partner_id.phone", string="Phone Number")
    user_email = fields.Char(related="list_report_id.create_uid.login", string="Email")
    user_company = fields.Char(related="list_report_id.create_uid.company_name", string="Company")
    description = fields.Text('Description', related='list_report_id.description', readonly=True)

    # Case Reported
    list_employee_report_ids = fields.One2many('wbs.report.emp', 'list_dir_report_id', domain="[('state','=','report_audit')]", string='Report Employee', copy=False)
    list_auditor_report_ids = fields.One2many('wbs.report.head', 'list_dir_report_id', string='Report Auditor', store=True,copy=False, readonly=True)
    name = fields.Char('Report Number', default="New", store=True, readonly=True)
    title = fields.Char('Report Title', default="New", store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Business Unit', store=True,copy=False, readonly=True)
    start_date = fields.Date('Start Date', store=True, readonly=True)
    end_date = fields.Date('End Date', store=True, readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', copy=False, readonly=True)
    
    @api.depends('employee_ids')
    def get_list_employee(self):
        department = self.env['mncei.department'].search([('name', '=', 'Internal Audit')]).id
        list_employee_wbs_ids = self.env['mncei.employee'].search([('department', '!=', department)]).ids + self.env['wbs.auditor'].search([]).mapped('head_audit_id').ids
        return list_employee_wbs_ids

    # Review By Director
    start_date_audit = fields.Date('Start Date Audit', store=True)
    end_date_audit = fields.Date('End Date Audit', store=True)
    employee_ids = fields.Many2many('mncei.employee', copy=False, string="Submit To", required=True)
    list_employee_wbs_ids = fields.Many2many('mncei.employee', 'list_employee_wbs_ids', copy=False, string="List Employee", default=get_list_employee)
    director_id = fields.Many2one('res.users', copy=False, string="Processed By", readonly=True)
    director_notes = fields.Text('Director Notes')
    dir_attachment_ids = fields.One2many('wbs.report.bod.attach', 'dir_id', copy=False, required=True)


    @api.onchange('dir_attachment_ids')
    def _check_dir_attachment_ids(self):
        for record in self:
            if len(record.dir_attachment_ids) > 15:
                raise ValidationError('You reached maximum attachments. Your maximal attachment is 15 files.')

    def change_state_to_close(self):
        """
        Method to change the state of draft lines to close
        and set the main record's state to close if all line_ids are closed.
        """
        for record in self:
            # Cek apakah semua line_ids sudah close
            if all(line.state == 'result_audit' for line in record.list_auditor_report_ids):
                record.state = 'result_audit'

    def change_state_to_process(self):
        """
        Method to change the state of draft lines to close
        and set the main record's state to close if all line_ids are closed.
        """
        for record in self:
            # Cek apakah semua line_ids sudah process
            if all(line.state == 'process_audit' for line in record.list_auditor_report_ids):
                record.state = 'process_audit'

    def assign_to_employee(self):
        Head_Audit = self.sudo().env['wbs.report.head']
        # Check Auditor
        head_audit_list = self.env['wbs.auditor'].search([]).mapped('head_audit_id')
        report_emp_ids = []
        if not self.employee_ids:
            raise ValidationError(_("Please input employee"))
        for employee in self.employee_ids:
            # Jika bukan head audit
            report_emp_id = False
            if employee.id not in head_audit_list.ids:
                # Revise Method
                vals = self.prepare_employee_value(employee)
                report_emp_id = Head_Audit.create(self.prepare_employee_value(employee))
                report_emp_id.write({
                    'is_not_auditor': True,
                    'head_auditor_id': employee.id,
                    'state': 'process_audit',
                })

            # Jika Head audit
            else:
                vals = self.prepare_employee_value(employee)
                master_audit = self.env['wbs.auditor'].search([('head_audit_id', '=', employee.id)])
                member = master_audit.auditor_1_ids.ids + master_audit.auditor_2_ids.ids + master_audit.auditor_3_ids.ids
                vals['member_ids'] = member
                vals['head_auditor_id'] = employee.id
                vals['master_head_auditor_id'] = master_audit.id
                report_emp_id = Head_Audit.create(vals)

            attch_ids = []
            Attachment = self.env['ir.attachment']
            if report_emp_id:
                for files in self.attachment_ids:
                    if files and files.name != '':
                        attachment_id = Attachment.create({
                            'name': files.name,
                            'type': 'binary',
                            'datas': files.datas,
                            'res_model': 'wbs.report.emp',
                            'res_id': report_emp_id.id
                        })
                        attch_ids.append(attachment_id.id)
                report_emp_id.update({
                    'attachment_ids': [(6, 0, attch_ids)],
                })
                # Revisi By Andi
                for file in self.dir_attachment_ids:
                    file.copy({
                        'dir_id': False,
                        'head_id': report_emp_id.id,
                    })
                report_emp_ids.append(report_emp_id)
            self.write({
                'state': 'assigned',
                'director_id': self.env.user.id,
            })
            template_id = self.env.ref('mnc_wbs.notification_to_head_audit_report_mail_template')
            user_ids = self.env['res.users'].search([('mncei_employee_id', 'in', employee.ids)])
            # To Send
            template = template_id.with_context(dbname=self._cr.dbname, invited_users=user_ids)
            template.sudo().send_mail(report_emp_id.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': employee.email})
        return True
    
    def confirm_close(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Close Report',
            'view_mode': 'form',
            'res_model': 'wbs.report.bod',
            'view_id': self.env.ref('mnc_wbs.confirmation_bod_form_view').id,
            'target': 'new',
            'context': {
                'form_view_initial_mode': 'edit',
                'create': '0',
                'delete': '0',
                'default_wbs_bod_id': self.id,
                # 'default_notes': self.head_auditor_notes,
            },
        }

    def button_close(self):
        self.list_report_id.state = 'Close'
        report = self.list_report_id

        template_id = self.env.ref('mnc_wbs.notification_complete_report_user_mail_template')
        # To Send
        template = template_id.with_context(dbname=self._cr.dbname, invited_users=report.create_uid)
        template.sudo().send_mail(report.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': report.create_uid.email})
        self.state = 'close'
        for employee in self.list_employee_report_ids:
            employee.button_close()

        for employee in self.list_auditor_report_ids:
            employee.button_close()
        return

    def button_cancel(self):
        self.list_report_id.state = 'Close'
        self.state = 'cancel'
        for employee in self.list_employee_report_ids:
            employee.button_cancel()

        for employee in self.list_auditor_report_ids:
            employee.button_cancel()
        return

    def prepare_employee_value(self, employee):
        vals = ({
            'employee_id': employee.id,
            'state': 'assigned',
            'list_report_id': self.list_report_id.id,
            'list_dir_report_id': self.id,
            'name': self.name,
            'title': self.title,
            'company_id': self.company_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'dir_notes': self.director_notes,
            'start_date_audit': self.start_date_audit,
            'end_date_audit': self.end_date_audit,
            'director_id': self.env.user.mncei_employee_id.id,
        })
        return vals

    def action_view_result(self):
        result = self.env['ir.actions.act_window']._for_xml_id('mnc_wbs.list_report_overview')
        result['flags'] = {'mode': 'readonly'}
        result['context'] = {
            'create': 0,
            'delete': 0,
            'edit': 0,
            'readonly': 1,
        }
        # choose the view_mode accordingly
        if len(self.list_auditor_report_ids) > 1:
            result['domain'] = [('list_dir_report_id', 'in', self.ids)]
        elif len(self.list_auditor_report_ids) <= 1:
            res = self.env.ref('mnc_wbs.list_report_head_result', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = self.list_auditor_report_ids.id
        return result
    
    def send_notif_new_report(self):
        template_id = self.env.ref('mnc_wbs.notification_new_report_wbs_mail_template')
        user_ids = self.sudo().env.ref('mnc_wbs.group_director_audit').users
        user_ids = list(set(user_ids))
        company_name = self.company_id.id
        company_name = self.env['res.company'].search([('id','in',[company_name])]).name
        # To Send
        for user in user_ids:
            template = template_id.with_context(dbname=self._cr.dbname, invited_users=user, company_name=company_name)
            template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})
    

class WBSReportBodAttachment(models.Model):
    _name = "wbs.report.bod.attach"

    dir_id = fields.Many2one('wbs.report.bod', store=True, copy=False)
    emp_id = fields.Many2one('wbs.report.emp', store=True, copy=False)
    head_id = fields.Many2one('wbs.report.head', store=True, copy=False)

    part_dokumen = fields.Binary(
        string='Dokumen Part',
        attachment=True
    )
    part_filename = fields.Char(
        string='Filename Part'
    )
