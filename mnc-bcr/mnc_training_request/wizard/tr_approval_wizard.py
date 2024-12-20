# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http


class MncPrApprovalWizard(models.TransientModel):
    """MNC Document Approval Wizard."""
    _name = "training.requisition.approval.wizard"
    _description = "Mnc TR Approval Wizard"

    choice_signature = fields.Selection([('upload', 'Upload Signature'),('draw', 'Draw Signature')], string="Sign with", default='draw')
    digital_signature = fields.Binary(string="Draw Signature")
    upload_signature = fields.Binary(string="Upload Signature")
    notes = fields.Text('Notes')
    current_uid = fields.Many2one(
        'res.users',
        string='Current Users', default=lambda self: self.env.user
    )
    upload_signature_fname = fields.Char(string='Upload Signature Name')
    reason_reject = fields.Text("Reason Rejected", store=True)
    uid_reject = fields.Many2one('res.users', "Reason Rejected", store=True, readonly=True)

    def action_approve(self):
        action = {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {'menu_id': self.env.ref('mnc_training_request.tr_menu_wait_approve').id},
            }
        tr_id = self.env['mncei.training.requesition'].browse(self._context.get('active_id'))
        if tr_id.is_hrga and not tr_id.is_ikatan_dinas:
            raise ValidationError(_("Please input Bond(Ikatan Dinas)"))
        if self.current_uid.id != tr_id.approve_uid.id:
            raise ValidationError(_("you are not user approved"))
        else:
            approval_id = tr_id.approval_id
            self.update_data_approval(approval_id)
            next_approver = self.env['mncei.training.req.approval'].search([
                ('id', '>', approval_id.id),
                ('tr_id', '=', tr_id.id),
            ], limit=1, order='id asc')
            if next_approver:
                tr_id.write({'approve_uid': next_approver.user_id.id, 'approval_id': next_approver.id, 'user_approval_ids': [(4, self.env.uid)]})
                tr_id.send_notif_approve(next_approver)
                return action
            else:
                tr_id.write({'user_approval_ids': [(4, self.env.uid)]})
                tr_id.to_approve()
                tr_id.send_notif_ga(approval_id)
                # raise ValidationError("X")
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
        tr_id = self.env['mncei.training.requesition'].browse(self._context.get('active_id'))
        if not self.reason_reject:
            raise ValidationError(_("Tolong tuliskan alasan mengapa TR ini di reject"))
        else:
            tr_id.write({
                'reason_reject': self.reason_reject,
                'state': 'reject',
                'uid_reject': self.current_uid.id
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_training_request.tr_menu_wait_approve').id},
        }
