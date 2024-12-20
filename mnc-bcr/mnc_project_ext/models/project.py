from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class ProjectStage(models.Model):
    _name = "project.stage"
    _description = "Project Stages"
    _order = 'sequence, id'

    active = fields.Boolean('Active', default=True)
    name = fields.Char("Name Stage", required=True, store=True)
    sequence = fields.Integer(default=100)
    description = fields.Text(translate=True)
    fold = fields.Boolean('Folded in Pipeline',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    is_closed = fields.Boolean('Closing Stage', help="Tasks in this stage are considered as closed.")


class Project(models.Model):
    _inherit = 'project.project'

    def _default_stage_id(self):
        """ Gives default stage_id """
        return self.stage_find([('fold', '=', False), ('is_closed', '=', False)])

    stage_id = fields.Many2one('project.stage', string='Stage',
        ondelete='restrict', tracking=True, index=True, copy=False,
        group_expand='_read_group_stage_ids', default=lambda self: self._default_stage_id())

    def stage_find(self, domain=[], order='sequence'):
        search_domain = []
        search_domain += list(domain)
        return self.env['project.stage'].search(search_domain, order=order, limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('fold', '=', False)]
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
