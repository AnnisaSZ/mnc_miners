from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError
from itertools import groupby

import logging

_logger = logging.getLogger(__name__)


class RateContractor(models.Model):
    _name = "rate.contractor"
    _description = "Rate Contractor"

    ttype = fields.Selection([
        ('hm', 'HM'),
        ('material', 'Material')
    ], default='hm', string="Rate Type", store=True)
    # HM
    contractor_id = fields.Many2one('fleet.sub.kontraktor', 'Contractor', store=True)
    group_unit = fields.Char('Group Unit', store=True)
    hm_minimum = fields.Float('HM Minimum')
    hm_formula = fields.Text('HM Formula')
    # Material
    distance = fields.Char('Distance', store=True)
    activity_id = fields.Many2one('master.activity', 'Activity', store=True)
    standard_fuel = fields.Char('Standard Fuel', store=True)
