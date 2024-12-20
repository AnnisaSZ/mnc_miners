from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class MasterJetty(models.Model):
    _inherit = 'master.jetty'

    company_ids = fields.Many2many('res.company', 'company_jetty_rel', 'company_id', 'jetty_id', string="Companies", store=True)

    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')