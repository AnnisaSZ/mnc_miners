from odoo import models, fields

class MnceiTrApproval(models.Model):
    _name = 'mncei.training.req.approval'
    _description = 'MNCEI TR Approval'
    _order = 'id asc'
    _rec_name = 'tr_id'

    tr_id = fields.Many2one('mncei.training.requesition', string='Training Request', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', store=True)
    email = fields.Char(string='Email', related='user_id.login', store=True)
    approve_date = fields.Datetime('Timestamp')
    is_email_sent = fields.Boolean('Email Sent')
    action_type = fields.Selection([('Approve','Approve'),('Reject','Reject')], string="Action Type", store=True)
    is_current_user = fields.Boolean('Approved', store=True)
    notes = fields.Text('Notes')
    reject_notes = fields.Text(string='Reject Notes')
    digital_signature = fields.Binary(string="Draw Signature")
    upload_signature = fields.Binary(string="Upload Signature")

    is_head_dept = fields.Boolean(string='Head Dept', store=True)
    is_bod = fields.Boolean( string='BOD', store=True)


class MnceiTrParticipant(models.Model):
    _name = 'mncei.training.req.participant'
    _description = 'Training Participant'

    nip = fields.Char(
        string='NIK', store=True, required=True
    )
    department_id = fields.Char(
        string='Department', store=True, required=True
    )
    name_participant = fields.Char(
        string='Participant', store=True, required=True
    )
    job_title = fields.Char(
        string='Position', store=True, required=True
    )


class MnceiTrAttachment(models.Model):
    _name = 'mncei.training.requesition.attachment'
    _description = 'MNCEI TR Attachment'
    _order = 'id asc'

    tr_id = fields.Many2one('mncei.training.requesition', string='Training Request', ondelete='cascade')
    attach_file = fields.Binary(string="Attachment")
    attach_name = fields.Char(string="Attachment Name")
