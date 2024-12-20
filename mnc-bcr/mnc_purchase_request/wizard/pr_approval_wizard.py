# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http


class MncPrApprovalWizard(models.TransientModel):
    """MNC Document Approval Wizard."""
    _name = "purchase.requisition.approval.wizard"
    _description = "Mnc PR Approval Wizard"

    choice_signature = fields.Selection([('upload', 'Upload Signature'),('draw', 'Draw Signature')], string="Sign with", default='draw')
    digital_signature = fields.Binary(string="Draw Signature")
    upload_signature = fields.Binary(string="Upload Signature")
    finance_attachment = fields.Binary(string="Attachment")
    notes = fields.Text('Notes')
    current_uid = fields.Many2one(
        'res.users',
        string='Current Users', default=lambda self: self.env.user
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company', store=True
    )
    upload_signature_fname = fields.Char(string='Upload Signature Name')
    finance_attachment_fname = fields.Char(string='Finance File Name')
    finance_uid = fields.Many2one('res.users', "Finance")
    is_procurement = fields.Boolean('Procurement')
    # Rejected
    reason_reject = fields.Text("Reason Rejected", store=True)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True)
    to_user_id = fields.Many2one('res.users', "User", store=True)
    to_requestor = fields.Boolean('Requestor')
    type_rejected = fields.Selection([('Requestor', 'Requestor'), ('Approval', 'Approval')], default='Approval', string="To", store=True)
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_user_wiz_rel', 'approval_wiz_id', 'user_id',
        string='Approvals', store=True, copy=False
    )

    def action_approve(self):
        action = {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_purchase_request.pr_menu_wait_approve').id},
        }
        pr_id = self.env['mncei.purchase.requisition'].browse(self._context.get('active_id'))
        if self.current_uid.id != pr_id.approve_uid.id:
            raise ValidationError(_("you are not user approved"))
        else:
            approval_id = pr_id.approval_id
            self.update_data_approval(approval_id)
            next_approver = self.env['mncei.purchase.requisition.approval'].search([
                ('id', '>', approval_id.id),
                ('pr_id', '=', pr_id.id),
            ], limit=1, order='id asc')
            if next_approver:
                if not next_approver.action_type:
                    pr_id.write({'approve_uid': next_approver.user_id.id, 'approval_id': next_approver.id, 'user_approval_ids': [(4, self.env.uid)]})
                    pr_id.send_notif_approve(next_approver)
                    if next_approver.is_procurement:
                        pr_id.to_procurement()
                    return action
                else:
                    next_approver = self.env['mncei.purchase.requisition.approval'].search([
                        ('id', '>', approval_id.id),
                        ('action_type', '=', 'Reject'),
                        ('pr_id', '=', pr_id.id),
                    ], limit=1, order='id asc')
                    pr_id.write({'approve_uid': next_approver.user_id.id, 'approval_id': next_approver.id, 'user_approval_ids': [(4, self.env.uid)]})
                    pr_id.send_notif_approve(next_approver)
                    if next_approver.is_procurement:
                        pr_id.to_procurement()
                    return action
            else:
                if not self.finance_uid:
                    raise ValidationError(_("Please Input User finance for followup this PR."))
                finance_approval_id = self.finance_data_approval(pr_id, self.finance_uid)
                pr_id.write({'approve_uid': self.finance_uid.id, 'approval_id': finance_approval_id.id, 'user_approval_ids': [(4, self.env.uid), (4, self.finance_uid.id)]})
                pr_id.to_approve(self.finance_uid, finance_approval_id)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                    'params': {'menu_id': self.env.ref('mnc_purchase_request.pr_menu_procurement').id},
                }

    def update_data_approval(self, line):
        if self.choice_signature == 'upload':
            if self.upload_signature_fname:
                # Check the file's extension
                tmp = self.upload_signature_fname.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('jpg', 'png', 'jpeg', 'JPG', 'JPEG', 'PNG'):
                    raise ValidationError(_("The file must be a images format file"))
                else:
                    self.prepare_data_approve(upload_signature=True)
                    line.write(self.prepare_data_approve(upload_signature=True))
        else:
            line.write(self.prepare_data_approve(digital_signature=True))

        return

    def prepare_data_approve(self, digital_signature=False, upload_signature=False, finance=False):
        if digital_signature:
            return {
                'digital_signature': self.digital_signature,
                'approve_date': fields.Datetime.now(),
                'notes': self.notes,
                'action_type': 'Approve',
                'is_current_user': True
            }
        if upload_signature:
            return {
                'upload_signature': self.upload_signature,
                'approve_date': fields.Datetime.now(),
                'notes': self.notes,
                'action_type': 'Approve',
                'is_current_user': True
            }
        if finance:
            return {
                'finance_attachment': self.finance_attachment,
                'finance_attachment_fname': self.finance_attachment_fname,
                'approve_date': fields.Datetime.now(),
                'notes': self.notes,
                'action_type': 'Approve',
                'is_current_user': True
            }

    def button_reject(self):
        pr_id = self.env['mncei.purchase.requisition'].browse(self._context.get('active_id'))
        if not self.reason_reject:
            raise ValidationError(_("Tolong tuliskan alasan mengapa PR ini di reject"))
        else:
            if self.type_rejected == 'Approval':
                current_approver_id = pr_id.approval_id
                approval_id = self.env['mncei.purchase.requisition.approval'].search([
                    ('id', '<', current_approver_id.id),
                    ('user_id', '=', self.to_user_id.id),
                    ('pr_id', '=', pr_id.id),
                ], limit=1, order='id asc')
                # Set Status Reject Current Approval
                reason = _('%s (To : %s)') % (self.reason_reject, self.to_user_id.name)
                current_approver_id.write({
                    'action_type': 'Reject',
                    'approve_date': fields.Datetime.now(),
                    'notes': reason,
                })
                # Update in User Re-Approve
                pr_id.write({
                    'approval_id': approval_id.id,
                    'approve_uid': self.to_user_id.id,
                })
                pr_id.send_notif_approve(approval_id)
            elif self.type_rejected == 'Requestor':
                pr_id.write({
                    'reason_reject': self.reason_reject,
                    'state': 'reject',
                    'uid_reject': self.current_uid.id,
                    'user_approval_ids': [(4, self.env.uid)]
                })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_purchase_request.pr_menu_wait_approve').id},
        }

    def finance_data_approval(self, pr_id, finance_uid):
        approval_id = self.env['mncei.purchase.requisition.approval'].create({
            'pr_id': pr_id.id,
            'user_id': self.env.uid,
            'email': self.env.user.login,
            'is_finance': True,
        })
        return approval_id

    def payment(self, pr_id):
        pr_id.approval_id.write(self.prepare_data_approve(finance=True))
        pr_id.write({
            'payment_state': 'payment',
            'state': 'payment',
            'finance_approval_ids': [(4, pr_id.approval_id.id)]
        })
        return

    def action_cancel_payment(self):
        pr_id = self.env['mncei.purchase.requisition'].browse(self._context.get('active_id'))
        if not self.notes:
            raise ValidationError(_("Tolong tuliskan catatan anda pada PR ini."))
        pr_id.approval_id.write(self.prepare_data_approve(finance=True))
        pr_id.write({
            'payment_state': 'cancel',
            'state': 'approve',
            'finance_approval_ids': [(4, pr_id.approval_id.id)]
        })
        return

    def finance_approve(self):
        pr_id = self.env['mncei.purchase.requisition'].browse(self._context.get('active_id'))
        if not self.notes or not self.finance_attachment:
            raise ValidationError(_("Tolong tuliskan catatan dan Attachment anda pada PR ini."))
        self.payment(pr_id)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_purchase_request.pr_menu_wait_approve').id},
        }
