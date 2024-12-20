from odoo import models, fields, api, _


class MnceiPerdinApproval(models.Model):
    _name = 'mncei.perdin.approval'
    _description = 'MNCEI Perdin Approval'
    _order = 'id asc'
    _rec_name = 'perdin_id'

    perdin_id = fields.Many2one('perjalanan.dinas.requestion.module', string='Perdin ID', ondelete='cascade')
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


class MnceiPerdinAttch(models.Model):
    _name = 'mncei.perdin.attachment'
    _description = 'MNCEI Perdin Attachment'
    _order = 'id asc'
    _rec_name = 'perdin_id'

    perdin_id = fields.Many2one('perjalanan.dinas.requestion.module', string='Perdin ID', ondelete='cascade')
    description = fields.Char('Description', store=True)
    attach_file = fields.Binary(string="Attachment")
    attach_name = fields.Char(string="Attachment Name")
