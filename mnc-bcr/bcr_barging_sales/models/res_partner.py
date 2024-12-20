from odoo import fields, api, models, _

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # def user_kontraktor(self):
    #     kontraktor_barge = self.env.ref('bcr_barging_sales.module_barge_sale_kontraktor_profit') or False
    #     print("XXXXXXXXXXXXXXXXx")
    #     return [('id', 'in', kontraktor_barge.users.ids)]

    # MASTER BUYER
    kode_buyer = fields.Char('Kode Buyer', readonly=False)
    area_ids = fields.Many2many(
        'master.area', string='PIT', domain="[('bu_company_id', '=', company_id)]", store=True)
    is_profit_sharing = fields.Boolean('Profit Sharing', store=True)
    user_profit_id = fields.Many2one('res.users', string="User Profit", store=True)
