from odoo import models, fields, api, _


class MnceiPrApproval(models.Model):
    _name = 'mncei.purchase.requisition.approval'
    _description = 'MNCEI PR Approval'
    _order = 'id asc'
    _rec_name = 'pr_id'

    pr_id = fields.Many2one('mncei.purchase.requisition', string='Purchase Request', ondelete='cascade')
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
    url = fields.Char(
        string='Url', related='pr_id.url', store=True
    )
    is_head_dept = fields.Boolean(
        string='Head Dept', store=True
    )
    is_bod = fields.Boolean(
        string='BOD', store=True
    )
    is_procurement = fields.Boolean(
        string='Procurement', store=True
    )
    is_finance = fields.Boolean(
        string='Finance', store=True
    )
    finance_attachment = fields.Binary(string="Attachment", store=True)
    finance_attachment_fname = fields.Char(string='Finance File Name')


class MnceiPrAtth(models.Model):
    _name = 'mncei.purchase.requisition.attachment'
    _description = 'MNCEI PR Attachment'
    _order = 'id asc'
    _rec_name = 'pr_id'

    pr_id = fields.Many2one('mncei.purchase.requisition', string='Purchase Request', ondelete='cascade')
    attach_file = fields.Binary(string="Attachment")
    attach_name = fields.Char(string="Attachment Name")
