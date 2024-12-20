from odoo import models, fields, api, _


class MnceiPerdinApproval(models.Model):
    _name = 'bcr.barging.approval'
    _description = 'BCR Barging Approval'
    _order = 'id asc'
    _rec_name = 'contract_id'

    contract_id = fields.Many2one('buyer.contract', string='Contract ID', ondelete='cascade')
    sales_plan_id = fields.Many2one('sales.plan', string='Sales Plan ID', ondelete='cascade')

    user_id = fields.Many2one('res.users', string='User', store=True)
    email = fields.Char(string='Email', related='user_id.login', store=True)
    approve_date = fields.Datetime('Timestamp')
    is_email_sent = fields.Boolean('Email Sent')
    action_type = fields.Selection([('Approve','Approve'),('Reject','Reject')], string="Action Type", store=True)
    is_current_user = fields.Boolean('Approved', store=True)
    notes = fields.Text('Notes')
    digital_signature = fields.Binary(string="Draw Signature")
    upload_signature = fields.Binary(string="Upload Signature")
