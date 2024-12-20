from odoo import models, fields, api, _


class PrfApproval(models.Model):
    _name = 'prf.approval'
    _description = 'Waiting Approval'
    _order = 'id asc'

    name = fields.Char('Name', compute='get_name_joined', store=True)
    prf_id = fields.Many2one('part.request', string='PRF', ondelete='cascade')
    orf_id = fields.Many2one('order.request', string='ORF', ondelete='cascade')
    po_id = fields.Many2one('purchase.order', string='PO', ondelete='cascade')
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

    @api.depends('prf_id', 'orf_id')
    def get_name_joined(self):
        for approval in self:
            name = '/'
            if approval.prf_id:
                name = approval.prf_id.name
            elif approval.orf_id:
                name = approval.orf_id.name
            approval.name = name
