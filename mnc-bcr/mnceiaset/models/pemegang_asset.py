from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PemegangAsset(models.Model):
    _name = 'pemegang.asset.groups'
    _description = 'Pemegang Asset'

    name = fields.Char("Pemegang Asset")
    employee_id = fields.Many2one('mncei.employee', store=True)
    asset_ids = fields.Many2many(
        'mnceiaset.module',
        string='Assets', store=True, compute='_get_assets'
    )
    count_asset = fields.Integer('Total Asset', store=True, compute='_get_assets')
    asset_line_ids = fields.One2many(
        'pemegang.aset',
        'groups_asset_line_id',
        string='Asset Line',
    )

    @api.depends('asset_line_ids', 'asset_line_ids.is_run', 'asset_line_ids.employee_id')
    def _get_assets(self):
        for user_asset in self:
            asset_ids = []
            for line in user_asset.asset_line_ids.filtered(lambda x: x.is_run):
                if line.aset_id.id not in asset_ids:
                    asset_ids.append(line.aset_id.id)
            user_asset.asset_ids = [(6, 0, asset_ids)]
            user_asset.count_asset = len(asset_ids)
