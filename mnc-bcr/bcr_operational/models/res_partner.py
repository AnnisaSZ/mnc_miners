from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        context = self.env.context
        if context.get('activity_id'):
            activity_id = self.env['master.activity'].browse(context.get('activity_id'))
            domain = [('is_kontraktor', '=', True), ('company_id', '=', context.get('company_id'))]
            domain += [('kontraktor_activity_ids', '=', activity_id.ids)]
        else:
            domain += ['|', ('display_name', operator, name), ('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()
