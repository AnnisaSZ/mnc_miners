from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import ast


class MnceiMeetingRoom(models.Model):
    _inherit = 'mncei.room.meeting'

    ga_dept_params_ids = fields.Many2many(
        'mncei.department', 'ga_dept_room_rel', 'params_id', 'ga_dept_id',
        string='GA Department', compute='_get_params_approval', copy=False)
    secretary_dept_params_ids = fields.Many2many(
        'mncei.department', 'secretaty_room_rel', 'params_id', 'secretary_dept_id',
        string='GA Department', compute='_get_params_approval', copy=False)

    @api.depends('name')
    def _get_params_approval(self):
        for meet_room in self:
            params_obj = self.env['ir.config_parameter']
            meet_room.ga_dept_params_ids = False
            meet_room.secretary_dept_params_ids = False
            # Get Value
            ga_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('ga_dept_id') or '[]')
            secretary_dept_params_ids = ast.literal_eval(params_obj.sudo().get_param('secretary_dept_id') or '[]')
            # Set Value
            meet_room.ga_dept_params_ids = [(6, 0, ga_dept_params_ids)]
            meet_room.secretary_dept_params_ids = [(6, 0, secretary_dept_params_ids)]
