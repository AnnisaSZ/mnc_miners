# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http


class MncPerdinApprovalWizard(models.TransientModel):
    """MNC Approval Wizard."""
    _name = "perdin.approval.wizard"
    _description = "Mnc Perdin Approval Wizard"

    choice_signature = fields.Selection([('upload', 'Upload Signature'),('draw', 'Draw Signature')], string="Sign with", default='draw')
    digital_signature = fields.Binary(string="Draw Signature")
    upload_signature = fields.Binary(string="Upload Signature")
    notes = fields.Text('Notes')
    current_uid = fields.Many2one(
        'res.users',
        string='Current Users', default=lambda self: self.env.user
    )
    upload_signature_fname = fields.Char(string='Upload Signature Name')
    # Rejected
    reason_reject = fields.Text("Reason Rejected", store=True)
    to_user_id = fields.Many2one('res.users', "User", store=True)
    type_rejected = fields.Selection([('Requestor', 'Requestor'), ('Approval', 'Approval')], default='Approval', string="To", store=True)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True)
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_user_perdin_wiz_rel', 'approval_perdin_wiz_id', 'user_id',
        string='Approvals', store=True, copy=False
    )

    def action_approve(self):
        action = {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_perjalanandinas.wait_approval_perdin_menu').id},
        }
        perdin_id = self.env['perjalanan.dinas.requestion.module'].browse(self._context.get('active_id'))
        if self.current_uid.id != perdin_id.approve_uid.id:
            raise ValidationError(_("you are not user approved"))
        else:
            approval_id = perdin_id.approval_id
            self.update_data_approval(approval_id)
            next_approver = self.env['mncei.perdin.approval'].search([
                ('id', '>', approval_id.id),
                ('perdin_id', '=', perdin_id.id),
            ], limit=1, order='id asc')
            if next_approver:
                if not next_approver.action_type:
                    perdin_id.send_notif_approve(next_approver)
                    perdin_id.write({'approve_uid': next_approver.user_id.id, 'approval_id': next_approver.id, 'user_approval_ids': [(4, self.env.uid)]})
                    return action
                else:
                    next_approver = self.env['mncei.perdin.approval'].search([
                        ('id', '>', approval_id.id),
                        ('action_type', '=', 'Reject'),
                        ('perdin_id', '=', perdin_id.id),
                    ], limit=1, order='id asc')
                    perdin_id.send_notif_approve(next_approver)
                    perdin_id.write({'approve_uid': next_approver.user_id.id, 'approval_id': next_approver.id, 'user_approval_ids': [(4, self.env.uid)]})
                    return action
            else:
                perdin_id.write({'user_approval_ids': [(4, self.env.uid)]})
                perdin_id.to_approve()
                return action

    def update_data_approval(self, line):
        if self.choice_signature == 'upload':
            if self.upload_signature_fname:
                # Check the file's extension
                tmp = self.upload_signature_fname.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('jpg', 'png', 'jpeg', 'JPG', 'JPEG', 'PNG'):
                    raise ValidationError(_("The file must be a images format file"))
                else:
                    line.write(self.prepare_data_approve(upload_signature=True))
        else:
            line.write(self.prepare_data_approve(digital_signature=True))

        return

    def prepare_data_approve(self, digital_signature=True, upload_signature=True):
        if digital_signature:
            return {
                'digital_signature': self.digital_signature,
                'approve_date': fields.Datetime.now(),
                'notes': self.notes,
                'action_type': 'Approve',
                'is_current_user': True
            }
        else:
            return {
                'upload_signature': self.upload_signature,
                'approve_date': fields.Datetime.now(),
                'notes': self.notes,
                'action_type': 'Approve',
                'is_current_user': True
            }

    def button_reject(self):
        perdin_id = self.env['perjalanan.dinas.requestion.module'].browse(self._context.get('active_id'))
        if not self.reason_reject:
            raise ValidationError(_("Tolong tuliskan alasan mengapa Dokumen ini di reject"))
        else:
            if self.type_rejected == 'Approval':
                current_approver_id = perdin_id.approval_id
                approval_id = self.env['mncei.perdin.approval'].search([
                    ('id', '<', current_approver_id.id),
                    ('user_id', '=', self.to_user_id.id),
                    ('perdin_id', '=', perdin_id.id),
                ], limit=1, order='id asc')
                # Set Status Reject Current Approval
                reason = _('%s (To : %s)') % (self.reason_reject, self.to_user_id.name)
                current_approver_id.write({
                    'action_type': 'Reject',
                    'approve_date': fields.Datetime.now(),
                    'notes': reason,
                })
                # Update in User Re-Approve
                perdin_id.write({
                    'approval_id': approval_id.id,
                    'approve_uid': self.to_user_id.id,
                })
                perdin_id.send_notif_approve(approval_id)
            elif self.type_rejected == 'Requestor':
                perdin_id.write({
                    'reason_reject': self.reason_reject,
                    'state': 'reject',
                    'uid_reject': self.current_uid.id
                })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_perjalanandinas.wait_approval_perdin_menu').id},
        }
