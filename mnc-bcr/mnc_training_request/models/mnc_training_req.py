from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class MnceiTrainingRequesition(models.Model):
    _name = 'mncei.training.requesition'
    _description = 'MNCEI Training Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_sequence(self):
        company = self.env.company
        sequence = self.env['ir.sequence'].with_company(company).next_by_code('training.code')
        return sequence or '/'

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    name = fields.Char("Name", store=True, default=_get_sequence)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    title_tr = fields.Char(
        string='Title', store=True, required=True
    )
    start_date = fields.Date(
        string='Start Date', store=True, required=True
    )
    end_date = fields.Date(
        string='End Date', store=True, required=True
    )
    address_tr = fields.Char(
        string='Address', store=True, required=True
    )
    organizer_tr = fields.Char(
        string='Organizer', store=True, required=True
    )
    speaker_tr = fields.Char(
        string='Speaker', store=True, required=True
    )
    cost_tr = fields.Float(
        string='Cost', store=True, required=True, digits='Cost Training'
    )
    objective_tr = fields.Text(
        string='Objective', store=True, required=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], string='Status', default='draft', store=True, required=True, copy=False, tracking=True)

    participant_ids = fields.Many2many(
        'mncei.employee', string='Participant',
        store=True
    )

    attach_ids = fields.One2many(
        'mncei.training.requesition.attachment','tr_id',
        string='Attachment List', store=True, ondelete='cascade'
    )

    user_approval_ids = fields.Many2many(
        'res.users', 'training_requesition_user_approval_rel', 'training_requesition_id', 'user_id',
        string='Approvals', store=True, copy=False
    )

    approve_uid = fields.Many2one(
        'res.users',
        string='User Approve', store=True, readonly=True
    )
    approval_id = fields.Many2one(
        'mncei.training.req.approval',
        string='Approval', store=True, readonly=True
    )
    approval_ids = fields.One2many('mncei.training.req.approval',
        'tr_id',
        string='Approval List', compute='add_approval', store=True, ondelete='cascade', copy=False
    )
    reason_reject = fields.Text("Reason Rejected", store=True)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True)

    # Approval
    requestor_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user,
        string='Requestor', store=True, required=True
    )
    head_request_id = fields.Many2one(
        'res.users',
        string='Head Requestor', store=True, required=True
    )
    spv_hr_id = fields.Many2one(
        'res.users',
        string='HR SPV', store=True, required=True
    )
    head_hrga_id = fields.Many2one(
        'res.users',
        string='Head HR/GA', store=True, required=True
    )
    accounting_dept_id = fields.Many2one(
        'res.users',
        string='Accounting', store=True, required=True
    )
    direksi1_id = fields.Many2one(
        'res.users',
        string='Operational Director', store=True, required=True
    )
    direksi2_id = fields.Many2one(
        'res.users',
        string='President Director', store=True
    )

    # Ikatan Dinas
    is_ikatan_dinas = fields.Boolean('Ikatan Dinas', store=True)
    duration_ikatan_dinas = fields.Integer("Durasi Ikatan Dinas(Year)", store=True, default=1)

    @api.depends('requestor_id', 'head_request_id', 'head_hrga_id', 'accounting_dept_id', 'direksi1_id', 'direksi2_id')
    def add_approval(self):
        for tr in self:
            tr.approval_ids = False
            approval_obj = self.env['mncei.training.req.approval']
            # Head User > GA > HRGA  > BOD Operational 
            if tr.requestor_id and tr.head_request_id and tr.head_hrga_id and tr.accounting_dept_id and tr.direksi1_id and tr.spv_hr_id:
                bod_list = [tr.direksi1_id.id]
                # Head Dept
                head_dept_list = [tr.head_request_id.id, tr.spv_hr_id.id, tr.head_hrga_id.id, tr.accounting_dept_id.id]
                approval_list = []
                # Optional Direksi 2
                if tr.direksi2_id:
                    bod_list.append(tr.direksi2_id.id)
                # Head Dept Create Approval
                for res_app in head_dept_list:
                    app_id = approval_obj.create(tr.prepare_data_approval(res_app, is_head_dept=True))
                    approval_list.append(app_id.id)
                # BOD Create Approval
                for bod_id in bod_list:
                    app_id = approval_obj.create(tr.prepare_data_approval(bod_id, is_bod=True))
                    approval_list.append(app_id.id)
                tr.approval_ids = [(6, 0, approval_list)]

    def prepare_data_approval(self, user_id, is_head_dept=False, is_bod=False):
        data = {
            'user_id': user_id,
        }
        if is_head_dept:
            data.update({
                'is_head_dept': True
            })
        if is_bod:
            data.update({
                'is_bod': True
            })
        return data

    @api.onchange('company_id')
    def change_sequence(self):
        self.name = self.env['ir.sequence'].with_company(self.company_id).next_by_code('training.code') or '/'

    # @api.model
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = f"{record.title_tr} ({record.company_id.name})"
    #         result.append((record.id, name))
    #     return result

    def send_notif_approve(self, next_approver=False):
        mail_template = self.env.ref('mnc_training_request.notification_training_request_mail_template_approved')
        if next_approver:
            mail_template.send_mail(next_approver.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': next_approver.user_id.login})
            next_approver.update({'is_email_sent': True})
        return True

    def send_notif_ga(self, last_approved=False):
        mail_template = self.env.ref('mnc_training_request.notification_training_request_ga')
        if last_approved:
            group_id = self.env.ref('mnc_hr.group_hr_mgr')
            for user in group_id.users.filtered(lambda x: last_approved.tr_id.company_id.id in x.company_ids.ids):
                mail_template.send_mail(last_approved.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': user.login})
        return True

    def action_approval(self):
        # Get data Approval Status paling atas, berdasarkan id // sorted, 1, 2, 3 , 4
        approval_uid = self.approval_ids.sorted(lambda x: x.id)[0]
        # Get data email template
        mail_template = self.env.ref('mnc_training_request.notification_training_request_mail_template_approved')
        # Jika nemu data approval
        if approval_uid:
            mail_template.send_mail(approval_uid.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': approval_uid.user_id.login})
            approval_uid.update({'is_email_sent': True})
            # update status pengajuan training ke Waiting jika approval uid ditemukan
            self.update({'state': 'waiting', 'approve_uid': approval_uid.user_id.id, 'approval_id': approval_uid.id})
        return True

    def action_sign_approve(self):
        signature_type = self.env.user.choice_signature
        upload_signature = False
        digital_signature = False
        if signature_type == 'upload':
            upload_signature = self.env.user.upload_signature
            if not upload_signature:
                raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        elif signature_type == 'draw':
            digital_signature = self.env.user.digital_signature
            if not digital_signature:
                raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        else:
            raise ValidationError(_("Please add your signature in Click Your name in Top Right > Preference > Signature"))
        return {
            'name': ("Sign & Approve"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'training.requisition.approval.wizard',
            'view_id': self.env.ref('mnc_training_request.mncei_tr_approval_wizard_form').id,
            'context': {'default_choice_signature': signature_type, 'default_digital_signature': digital_signature, 'default_upload_signature': upload_signature}
        }

    def open_reject(self):
        return {
            'name': ("Reason Rejected"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'training.requisition.approval.wizard',
            'view_id': self.env.ref('mnc_training_request.reject_tr_view_form').id,
        }

    def set_draft(self):
        for line in self.approval_ids:
            line.update({
                'is_email_sent': False,
                'is_current_user': False,
                'approve_date': False,
            })
        self.update({'state': 'draft'})
        return

    def to_approve(self):
        self.update({
            'state': 'approve',
        })
        return

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

    def _compute_is_hrga(self):
        for record in self:
            if record.spv_hr_id == self.env.user:
                record.is_hrga = True
            else:
                record.is_hrga = False

    is_creator = fields.Boolean(string="Is Creator", default=True, compute='_compute_is_creator')
    is_approved = fields.Boolean(string="Is Approved", default=True, compute='_compute_is_approved')
    is_hrga = fields.Boolean(string="Is HRGA", default=False, compute='_compute_is_hrga')

    @api.constrains('start_date', 'end_date')
    def _check_validation_date(self):
        for training in self:
            if training.start_date > training.end_date:
                raise ValidationError(_("End Date harus lebih besar dari Start Date"))
            if training.start_date <= fields.Date.today():
                raise ValidationError(_("Start Date harus lebih besar dari hari ini"))
