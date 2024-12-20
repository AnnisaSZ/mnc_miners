from odoo import models, fields, api, _


class PriceApproval(models.Model):
    _name = 'price.approval'
    _description = 'Waiting Approval'
    _order = 'id asc'

    name = fields.Char('Name', compute='get_name_joined', store=True)
    pc_id = fields.Many2one('price.comparation', string='Price Comparison', ondelete='cascade')
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

    @api.depends('pc_id')
    def get_name_joined(self):
        for approval in self:
            name = '/'
            if approval.pc_id:
                name = approval.pc_id.name
            elif approval.pc_id:
                name = approval.pc_id.name
            approval.name = name
