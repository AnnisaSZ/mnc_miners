# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError

class PrfApprovalWizard(models.TransientModel):
    """MNC Document Approval Wizard."""
    _name = "slp.approval.wizard"
    _description = "SLP Approval Wizard"

    name = fields.Char('name')
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
    user_approval_ids = fields.Many2many(
        'res.users', 'approval_user_wiz_slp_rel', 'approval_wiz_scm_id', 'user_id',
        string='Approvals', store=True, copy=False
    )
    slp_id = fields.Many2one('submission.letter.payment')    

    def action_approve(self):
        models = self._context.get('active_model')
        domain = False
        
        slp_id = self.env[models].browse(self._context.get('active_id'))
        if self.current_uid.id != slp_id.approve_uid.id:
            raise ValidationError(_("you are not user approved"))
        else:
            approval_id = slp_id.approval_id
            self.update_data_approval(approval_id)
            next_approver = False
            domain = [('id', '>', approval_id.id), ('slp_id', '=', slp_id.id),]
            next_approver = self.env['slp.approval'].search(domain, limit=1, order='id asc')
            if next_approver:
                slp_id.write({'approve_uid': next_approver.user_id.id, 'approval_id': next_approver.id, 'user_approval_ids': [(4, self.env.uid)]})
                slp_id.send_notif_approve(next_approver)
                # return action
            else:
                slp_id.write({'state': 'progress'})
                # slp_id.send_notif_done()

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

    def prepare_data_approve(self, digital_signature=False, upload_signature=False):
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

    def action_reject(self):
        action = {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_scm.order_request_menu').id},
        }
        if not self.reason_reject:
            raise ValidationError(_("Tolong tuliskan alasan mengapa PR ini di reject"))
        else:
            models = self._context.get('active_model')
            state = 'cancel'
            slp_id = self.env[models].browse(self._context.get('active_id'))
            slp_id.write({
                'reason_reject': self.reason_reject,
                'state': state,
                'uid_reject': self.current_uid.id,
                'user_approval_ids': [(4, self.env.uid)]
            })
            slp_id.approval_id.write({'notes': 'reject: ' + self.reason_reject})
            slp_id.action_reject()

        return action
