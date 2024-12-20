from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging

TIMEOUT = 20

_logger = logging.getLogger(__name__)


class QontakTemplate(models.Model):
    _name = "qontak.template"

    auth_id = fields.Many2one('qontak.auth', string="Auth")
    qontak_id = fields.Char('Qontak ID')
    organization_id = fields.Char('Organization')
    name = fields.Char('Name')
    body = fields.Text('Body')
    status = fields.Char('Status')
    category = fields.Char('Category')

    def open_body(self):
        return {
            'name': _("Body Messages"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'qontak.template',
            'res_id': self.id,
            'view_id': self.env.ref('mnc_wa_api.qontak_template_form').id,
        }
