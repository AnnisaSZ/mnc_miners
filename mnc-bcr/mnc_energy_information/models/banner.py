from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
# from PIL import Image
# from io import BytesIO
# import base64


class MnceiBanner(models.Model):
    _name = 'mncei.banner'
    _description = 'MNCEI Banner'
    _rec_name = 'title'
    _order = 'id desc'

    title = fields.Char('Title', store=True, required=True, copy=False)
    description = fields.Text('Description', store=True, copy=False)
    banner_img = fields.Image('Banner', store=True, required=True, copy=False)
    detail_img = fields.Image('Detail Image', store=True, required=True, copy=False)
    date_start = fields.Date('Date Start', default=fields.Date.today(), store=True, required=True, copy=False)
    date_end = fields.Date('Date End', default=fields.Date.today(), store=True, required=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('release', 'Release'),
        ('expired', 'Expired'),
        ('reject', 'Reject'),
        ('revise', 'Revise'),
    ], default='draft', string='State', store=True, copy=False)
    link = fields.Char('Link', store=True)

    @api.constrains('date_start', 'date_end')
    def check_date_duration(self):
        for banner in self:
            if banner.date_start > banner.date_end:
                raise ValidationError(_("Please input date start bigger than end date"))

    def action_to_expired(self):
        banner_ids = self.env['mncei.banner'].search([('date_end', '<=', fields.Date.today())])
        for banner_id in banner_ids:
            banner_id.update({
                'state': 'expired'
            })

    def action_submit(self):
        self.update({
            'state': 'waiting'
        })
        return

    def action_approve(self):
        self.update({
            'state': 'release'
        })
        return

    def action_reject(self):
        self.update({
            'state': 'reject'
        })
        return

    def action_revise(self):
        self.update({
            'state': 'revise'
        })
        return

    def action_extend(self):
        return {
            'name': _("Extend"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'cms.extend.wizard',
            'view_id': self.env.ref('mnc_energy_information.extend_wizard_form').id,
            'context': {
                'default_banner_id': self.id
            },
        }

    # Method ketika saat di list view create split emails
    @api.model
    def create(self, vals):
        res = super(MnceiBanner, self).create(vals)
        if vals.get('banner_img'):
            res.add_attachment(res, vals.get('banner_img'), 'banner_img')
        if vals.get('detail_img'):
            self.add_attachment(res, vals.get('detail_img'), 'detail_img')
        return res

    def write(self, values):
        res = super(MnceiBanner, self).write(values)
        if values.get('banner_img'):
            self.add_attachment(self, values.get('banner_img'), 'banner_img')
        if values.get('detail_img'):
            self.add_attachment(self, values.get('detail_img'), 'detail_img')
        return res

    # -------- To Create Attachment ------
    def add_attachment(self, res_id, filename, res_field):
        domain = [('res_id', '=', res_id.id), ('res_model', '=', 'mncei.banner'), ('res_field', '=', res_field)]
        attachment_id = self.env['ir.attachment'].search(domain, limit=1)
        print("XXXXXXXXXXXXXXXXXX")
        print(attachment_id)
        print(attachment_id)
        if attachment_id:
            attachment_id.write({
                'datas': filename,
                'public': True,
            })
            attachment = attachment_id
        else:
            attachment = self.env['ir.attachment'].create(
                {
                    'name': f"[{res_field}] {res_id.title}",
                    'company_id': False,
                    'public': True,
                    'type': 'binary',
                    'datas': filename,
                    'res_model': 'mncei.banner',
                    'res_id': res_id.id,
                    'res_field': res_field
                })
        return attachment
