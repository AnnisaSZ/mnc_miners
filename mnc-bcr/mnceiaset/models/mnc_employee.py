from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'mncei.employee'

    asset_ids = fields.Many2many(
        'mnceiaset.module',
        string='Assets', compute='_get_assets', store=True
    )
    count_asset = fields.Integer('Total Asset', compute='_get_assets',store=True)
    asset_line_ids = fields.One2many(
        'pemegang.aset',
        'employee_id',
        string='Asset Line',
    )

    @api.depends('asset_line_ids', 'asset_line_ids.is_run')
    def _get_assets(self):
        for employee in self:
            asset_ids = []
            for line in employee.asset_line_ids.filtered(lambda x: x.is_run):
                if line.aset_id.id not in asset_ids:
                    asset_ids.append(line.aset_id.id)
            employee.asset_ids = [(6, 0, asset_ids)]
            employee.count_asset = len(asset_ids)

    def action_open_asset(self):
        return {
            'name': _("List Asset"),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'mnceiaset.module',
            'view_id': self.env.ref('mnceiaset.mnceiaset_view_form').id,
            'domain': [('id', 'in', self.asset_ids.ids)],
            'views': [[self.env.ref('mnceiaset.mnceiaset_view_tree').id, 'list'], [self.env.ref('mnceiaset.mnceiaset_view_form').id, 'form']],
        }


class HrDepartment(models.Model):
    _inherit = 'mncei.department'

    asset_ids = fields.Many2many(
        'mnceiaset.module',
        string='Assets', compute='_get_assets', store=True
    )
    count_asset = fields.Integer('Total Asset', compute='_get_assets',store=True)
    employee_ids = fields.One2many(
        'mncei.employee',
        'department',
        string='Employees',
    )

    @api.depends('employee_ids')
    def _get_assets(self):
        for department in self:
            asset_ids = []
            for employee in department.employee_ids:
                for asset_id in employee.asset_ids:
                    asset_ids.append(asset_id.id)
            department.asset_ids = [(6, 0, asset_ids)]
            department.count_asset = len(asset_ids)

    def action_open_asset(self):
        return {
            'name': _("List Asset"),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'mnceiaset.module',
            'view_id': self.env.ref('mnceiaset.mnceiaset_view_form').id,
            'domain': [('id', 'in', self.asset_ids.ids)],
            'views': [[self.env.ref('mnceiaset.mnceiaset_view_tree').id, 'list'], [self.env.ref('mnceiaset.mnceiaset_view_form').id, 'form']],
        }

