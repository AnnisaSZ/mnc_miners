from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime, date

import logging

_logger = logging.getLogger(__name__)


class TypePlanningOption(models.Model):
    _name = 'planning.type.option'
    _description = 'Planning Type Option'

    name = fields.Char("Planning Name", store=True, required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], string='Status', default='active', store=True, required=True)
    period_id = fields.Many2one('planning.type.period', string="Period", store=True)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        context = self.env.context
        if context.get('plan_id'):
            plan_id = self.env['planning.opr'].browse(context.get('plan_id'))
            if plan_id.is_yearly:
                domain += [('period_id.name', 'ilike', 'yearly'), ('status', '=', 'active')]
            elif plan_id.is_monthly:
                domain += [('period_id.name', 'ilike', 'monthly'), ('status', '=', 'active')]
        if context.get('type_period'):
            type_period = context.get('type_period')
            if type_period == 'Yearly':
                domain += [('period_id.name', 'ilike', 'yearly'), ('status', '=', 'active')]
            elif type_period == 'Monthly':
                domain += [('period_id.name', 'ilike', 'monthly'), ('status', '=', 'active')]
        else:
            domain += [('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()


class TypePlanningPeriod(models.Model):
    _name = 'planning.type.period'
    _description = 'Planning Type Period'

    name = fields.Char("Planning Name", store=True, required=True)
    option_ids = fields.One2many('planning.type.option', 'period_id', string="Options", store=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], string='Status', default='active', store=True, required=True)


class TsAdb(models.Model):
    _name = 'ts.adb'
    _description = 'TS ADB'

    name = fields.Char('TS ADB', store=True, required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], string='Status', default='active', store=True, required=True)
