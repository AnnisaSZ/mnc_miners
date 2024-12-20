from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

from odoo.addons.bcr_planning_custom_sh.models.model import cek_date_lock_act, cek_date_lock_act_message

import logging

_logger = logging.getLogger(__name__)


class InheritActStockroom(models.Model):
    _name = 'act.stockroom'
    _order = 'date_act desc'
    _inherit = ['act.stockroom', 'mail.thread', 'mail.activity.mixin']

    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', domain="[('code', 'in', ['IN-MA', 'IN-ME'])]", required=True)
    area_id = fields.Many2one('master.area', string='PIT', required=True)
    seam_id = fields.Many2one('master.seam', string='Seam', required=True)
    # to_revise = fields.Boolean('Revise', store=True)
    state = fields.Selection(tracking=True)

    # Button Submit and Revise
    def action_submit(self):
        for act_stockroom in self:
            if cek_date_lock_act("input", self.env.user.id, act_stockroom.date_act):
                raise UserError(cek_date_lock_act_message("input"))
            if act_stockroom.state == 'draft':
                act_stockroom.write({
                    'state': 'complete'
                })
            return

    def action_revise(self):
        for act_stockroom in self:
            if act_stockroom.state == 'complete':
                act_stockroom.write({
                    'state': 'draft',
                })
        return

    # @api.constrains('date_act')
    # def _check_date_act(self):
    #     for act_stockroom in self:
    #         if cek_date_lock_act("input", self.env.user.id, act_stockroom.date_act) and act_stockroom.state == 'draft':
    #             raise UserError(cek_date_lock_act_message("input"))
