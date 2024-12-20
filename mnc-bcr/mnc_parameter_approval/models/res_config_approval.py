# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResConfigApproval(models.Model):
    _name = 'res.config.approval'
    _description = "Setting Approval"

    model_type = fields.Selection([
        ('perdin', 'Perdin'),
        ('purchase_request', 'Purchase Request'),
        ('training', 'Training'),
    ], string='Model', store=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', store=True, required=True)

    # Approval
    ga_id = fields.Many2one(
        'res.users',
        string='GA', store=True, copy=False
    )
    head_hrga_id = fields.Many2one(
        'res.users',
        string='Head HR/GA', store=True, copy=False
    )
    direksi1_id = fields.Many2one(
        'res.users',
        string='Direksi 1', store=True, copy=False
    )
    direksi2_id = fields.Many2one(
        'res.users',
        string='Direksi 2', store=True, copy=False
    )
    direksi3_id = fields.Many2one(
        'res.users',
        string='Direksi 3', store=True, copy=False
    )
    # PR
    head_finance_id = fields.Many2one(
        'res.users',
        string='Head Finance', store=True, copy=False
    )
    procurement_id = fields.Many2one(
        'res.users',
        string='Procurement', store=True, copy=False
    )
    # Training
    hr_id = fields.Many2one(
        'res.users',
        string='HR', store=True, copy=False
    )
    accounting_id = fields.Many2one(
        'res.users',
        string='Accounting', store=True, copy=False
    )
    # Dinas
    spv_id = fields.Many2one(
        'res.users',
        string='Supervisor', store=True, copy=False
    )

    def name_get(self):
        result = []
        for res_approval in self:
            model_type = dict(self._fields['model_type'].selection).get(self.model_type)
            name = _("[%s] - %s") % (model_type, res_approval.company_id.name)
            result.append((res_approval.id, name))
        return result
