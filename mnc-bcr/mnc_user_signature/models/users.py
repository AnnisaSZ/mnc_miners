from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    choice_signature = fields.Selection([('upload', 'Upload Signature'),('draw', 'Draw Signature')], string="Sign with", default='draw', store=True, copy=False)
    digital_signature = fields.Binary(string="Draw Signature", store=True, copy=False)
    upload_signature = fields.Binary(string="Upload Signature", store=True, copy=False)
    upload_signature_fname = fields.Char(string='Upload Signature Name', copy=False)

    @api.constrains('choice_signature', 'upload_signature_fname')
    def _check_user_signature(self):
        for user in self:
            if user.choice_signature == 'upload':
                if user.upload_signature_fname:
                    tmp = user.upload_signature_fname.split('.')
                    ext = tmp[len(tmp)-1]
                    if ext not in ('jpg', 'png', 'jpeg', 'JPG', 'JPEG', 'PNG'):
                        raise ValidationError(_("The file must be a images format file"))
