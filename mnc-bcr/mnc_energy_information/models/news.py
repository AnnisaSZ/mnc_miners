from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from PIL import Image
from io import BytesIO

import base64


class MnceiBanner(models.Model):
    _name = 'mncei.news'
    _description = 'MNCEI News'
    _rec_name = 'title'
    _order = 'id desc'

    title = fields.Char('Title', store=True, required=True, copy=False)
    description = fields.Text('Description', store=True, copy=False)
    thumbnail = fields.Text('Thumbnails', store=True, copy=False)
    thumb_img = fields.Image('Thumbnails Image', store=True, required=True, copy=False)
    news_img = fields.Image('News Image', store=True, required=True, copy=False)
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

    @api.constrains('date_start', 'date_end')
    def check_date_duration(self):
        for banner in self:
            if banner.date_start > banner.date_end:
                raise ValidationError(_("Please input date start bigger than end date"))

    @api.constrains('thumb_img', 'news_img')
    def check_image_dimensions(self):
        thumb_ratio = 16 / 9
        news_img = 4 / 3
        for news in self:
            # Check Thumbnail Image
            if news.news_img:
                image = Image.open(BytesIO(base64.b64decode(news.news_img)))
                # Dapatkan dimensi gambar
                width, height = image.size
                if abs((width/height) - thumb_ratio) > 0.1:
                    raise ValidationError(_("Image must be ratio 16:9"))
            if news.thumb_img:
                image = Image.open(BytesIO(base64.b64decode(news.thumb_img)))
                # Dapatkan dimensi gambar
                width, height = image.size
                if abs((width/height) - news_img) > 0.1:
                    raise ValidationError(_("Image must be ratio 4:3"))

    def action_to_expired(self):
        news_ids = self.env['mncei.news'].search([('date_end', '<=', fields.Date.today())])
        for news_id in news_ids:
            news_id.update({
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
                'default_news_id': self.id
            },
        }

    # Method ketika saat di list view create split emails
    @api.model
    def create(self, vals):
        res = super(MnceiBanner, self).create(vals)
        if vals.get('thumb_img'):
            res.add_attachment(res, vals.get('thumb_img'), thumbnail=True)
        if vals.get('news_img'):
            res.add_attachment(res, vals.get('news_img'))
        return res

    def write(self, values):
        res = super(MnceiBanner, self).write(values)
        if values.get('thumb_img'):
            self.add_attachment(self, values.get('thumb_img'), thumbnail=True)
        if values.get('news_img'):
            self.add_attachment(self, values.get('news_img'))
        return res

    # -------- To Create Attachment ------
    def add_attachment(self, res_id, filename, thumbnail=False):
        domain = [('res_id', '=', res_id.id), ('res_model', '=', 'mncei.news')]
        if thumbnail:
            domain += [('res_field', '=', 'thumb_img')]
        else:
            domain += [('res_field', '=', 'news_img')]
        attachment_id = self.env['ir.attachment'].search(domain, limit=1)
        if attachment_id:
            attachment_id.write({
                'datas': filename,
                'public': True,
            })
            attachment = attachment_id
        else:
            attachment = self.env['ir.attachment'].create(
                {
                    'name': res_id.title,
                    'company_id': False,
                    'public': True,
                    'type': 'binary',
                    'datas': filename,
                    'res_model': 'mncei.news',
                    'res_id': res_id.id
                })
            if thumbnail:
                attachment.write({
                    'res_field': 'thumb_img'
                })
            else:
                attachment.write({
                    'res_field': 'news_img'
                })
        return attachment
