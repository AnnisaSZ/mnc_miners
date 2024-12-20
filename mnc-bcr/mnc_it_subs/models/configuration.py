from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MasterLocation(models.Model):
    _name = 'master.location.itsubs'
    _description = 'Master Location'
    _order = 'id desc'

    name = fields.Char('Name', store=True, required=True, copy=False)
    active = fields.Boolean('Status', store=True, default=True)

class MasterStatus(models.Model):
    _name = 'master.status.itsubs'
    _description = 'Master Status'
    _order = 'id desc'

    name = fields.Char('Name', store=True, required=True, copy=False)
    active = fields.Boolean('Status', store=True, default=True)

class MasterSubsType(models.Model):
    _name = 'master.type.itsubs'
    _description = 'Master Subscription Type'
    _order = 'id desc'

    name = fields.Char('Name', store=True, required=True, copy=False)
    classification = fields.Selection([
        ('software', 'Software'),
        ('hardware', 'Hardware'),
     ], string='Classification', default='software', required=True, store=True, copy=False)
    active = fields.Boolean('Status', store=True, default=True)

class MasterSubsVendor(models.Model):
    _name = 'master.vendor.itsubs'
    _description = 'Master IT Subscription Vendor'
    _order = 'id desc'

    name = fields.Char('Name', store=True, required=True, copy=False)
    subs_type_id = fields.Many2one('master.type.itsubs', string='Subscription Type', store=True, required=True, copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, required=True)
    contact = fields.Char('PIC', store=True, required=True, copy=False)
    email = fields.Char('Email', store=True, required=True, copy=False)
    tel = fields.Char('No. Telp', store=True, required=True, copy=False)
    first_agreement = fields.Date('First Agreement', store=True, copy=False)
    attachment = fields.Binary('Attachments', attachment=True)
    filename_attachment = fields.Char('Name Attachments', store=True)
    active = fields.Boolean('Status', store=True, default=True)

    @api.constrains('attachment')
    def check_attachment(self):
        for form in self:
            if form.attachment:
                tmp = form.filename_attachment.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF', 'png', 'PNG'):
                    raise ValidationError(_("The file must be a PDF/PNG format file"))


