# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError

class PrfApprovalWizard(models.TransientModel):
    """MNC Document Approval Wizard."""
    _name = "prf.approval.wizard"
    _description = "PRF Approval Wizard"

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
        'res.users', 'approval_user_wiz_scm_rel', 'approval_wiz_scm_id', 'user_id',
        string='Approvals', store=True, copy=False
    )
    po_id = fields.Many2one('purchase.order')

    def action_approve(self):
        action = False
        menu_id = False
        models = self._context.get('active_model')
        domain = False
        state = ''
    
        if models == 'purchase.order':
            menu_id = self.env.ref('mnc_scm.po_menu').id
            state = 'unpaid'
        else:
            menu_id = self.env.ref('mnc_scm.order_request_menu').id
            state = 'approve'
        menu_id = self.env.ref('mnc_scm.order_request_menu').id
        action = {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_scm.order_request_menu').id},
        }
        orf_id = self.env[models].browse(self._context.get('active_id'))

        if models != 'purchase.order':
            if self.current_uid.id != orf_id.approve_uid.id:
                raise ValidationError(_("you are not user approved"))
        approval_id = orf_id.approval_id
        self.update_data_approval(approval_id)
        next_approver = False

        if models == 'purchase.order':
            domain = [('id', '>', approval_id.id), ('po_id', '=', orf_id.id),]
        else:
            domain = [('id', '>', approval_id.id), ('orf_id', '=', orf_id.id),]
        next_approver = self.env['prf.approval'].search(domain, limit=1, order='id asc')
        if next_approver:
            orf_id.write({'approve_uid': next_approver.user_id.id, 'approval_id': next_approver.id, 'user_approval_ids': [(4, self.env.uid)]})
            orf_id.send_notif_approve(next_approver)
            # return action
        else:
            # Take Out SLP
                # if len(orf_id.approval_ids.filtered(lambda x: x.is_current_user))>3:
                #     orf_id.generate_payment()
                #     orf_id.write({'state': 'done'})
                # else:
            orf_id.write({'state': state})
            orf_id.send_notif_done()
            # return action

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
            state = 'reject'
            orf_id = self.env[models].browse(self._context.get('active_id'))
            if models == 'purchase.order' or models == 'submission.letter.payment':
                state = 'cancel'
            orf_id.write({
                'reason_reject': self.reason_reject,
                'state': state,     
                'uid_reject': self.current_uid.id,
                'user_approval_ids': [(4, self.env.uid)]
            })
            orf_id.send_notif_reject()
            if models == 'order.request':
                orf_id.action_cancel()
        # return action
    
    def action_cancel(self):
        action = {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mnc_scm.order_request_menu').id},
        }
        if not self.reason_reject:
            raise ValidationError(_("Tolong tuliskan alasan mengapa PR ini di reject"))
        else:
            models = self._context.get('active_model')
            state = 'reject'
            orf_id = self.env[models].browse(self._context.get('active_id'))
            if models == 'purchase.order' or models == 'submission.letter.payment':
                state = 'cancel'
            orf_id.write({
                'reason_reject': self.reason_reject,
                'state': state,     
                'uid_reject': self.current_uid.id,
                'user_approval_ids': [(4, self.env.uid)]
            })
            orf_id.action_cancel()
        return action
