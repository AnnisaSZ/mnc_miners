# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http


class CMSExtend(models.TransientModel):
    """MNC Document Approval Wizard."""
    _name = "cms.extend.wizard"
    _description = "CMS Extend Wizard"

    banner_id = fields.Many2one('mncei.banner', 'Banner')
    news_id = fields.Many2one('mncei.news', 'News')
    extend_date = fields.Date('To Date', required=True)

    def action_to_extend(self):
        if self.extend_date < fields.Date.today():
            raise ValidationError(_("Extend Date must be > Today"))
        data = {
            'date_end': self.extend_date,
            'state': 'release'
        }
        if self.banner_id:
            self.banner_id.update(data)
        elif self.news_id:
            self.banner_id.update(data)
        return True
