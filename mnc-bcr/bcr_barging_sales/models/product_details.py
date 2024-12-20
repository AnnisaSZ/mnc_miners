from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date

import logging

_logger = logging.getLogger(__name__)


class ProductDetails(models.Model):
    _name = "product.detail"
    _description = 'Product Details'
    _rec_name = "id"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    active = fields.Boolean('Active', store=True, default=True)
    company_id = fields.Many2one('res.company', force_save='1', string='Bisnis Unit', required=True, default=lambda self: (self.env.company.id), domain=_company_ids_domain)
    # Shipping
    shipping_id = fields.Many2one('sales.shipping', 'Shipping', domain="[('company_id', '=', company_id)]", required=True, store=True)
    mv_id = fields.Many2one('master.mv', string='MV Name', store=True)
    barge_lineup_id = fields.Many2one('barge.lineup', string="Barge Lineup", store=True, domain="[('shipping_id', '=', shipping_id)]")
    # Barge Detail
    barge_detail_id = fields.Many2one('barge.detail', string='Barge Detail', store=True, domain="[('shipping_id', '=', shipping_id), ('state', '=', 'draft')]")
    market_type = fields.Selection([
        ('export', 'Export'),
        ('domestic', 'Domestic'),
    ], default='export', string='Market', store=True, required=True, tracking=True)
    # Information
    barge_id = fields.Many2one('master.barge', string='Barge Name', store=True, required=True)
    buyer_id = fields.Many2one('res.partner', string="Buyer", store=True, required=True, domain="[('is_buyer', '=', True)]")

    activity_id = fields.Many2one('master.activity', string='Activity', domain="[('code', '=', '01-BG')]", required=True)
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', store=True, required=True, domain="[('activity_id', '=', activity_id)]")
    loading_date = fields.Date('Loading Date', store=True, required=True)
    sizing = fields.Selection([
        ('sizing', 'Sizing'),
        ('no_sizing', 'No Sizing'),
    ], default='sizing', string='Sizing', store=True, required=True)
    source_group = fields.Selection([
        ('pit', 'PIT'),
        ('rom', 'ROM'),
        ('stockpile', 'Stockpile Port'),
    ], default='pit', string='Source Group', store=True, required=True)
    source_group_id = fields.Many2one('master.sourcegroup', string='Source Group', compute='_get_source_group')
    source_id = fields.Many2one('master.source', string='Source', domain="[('source_group_id', '=', source_group_id), ('bu_company_id', 'in', jetty_company_ids)]", store=True, required=True, states={'draft': [('required', True)]})
    jetty_id = fields.Many2one('master.jetty', string='Jetty Name', domain="[('company_ids', 'in', company_id)]", required=True, store=True)
    jetty_company_ids = fields.Many2many('res.company', related="jetty_id.company_ids")
    area_id = fields.Many2one('master.area', string='PIT', domain="[('bu_company_id', 'in', jetty_company_ids)]", required=True, store=True)
    seam_id = fields.Many2one('master.seam', string='Seam Code', store=True, domain="[('area_id', '=', area_id)]")
    kontraktor_barging_id = fields.Many2one('res.partner', string='Kontraktor Barging', store=True, required=True, domain="[('kontraktor_activity_ids.code', '=', '01-BG'), ('company_id', '=', company_id)]")
    kontraktor_product_id = fields.Many2one('res.partner', string='Kontraktor Produksi', store=True, required=True, domain="[('kontraktor_activity_ids.code', '=', '01-PR'), ('company_id', 'in', jetty_company_ids)]")

    shift_id = fields.Many2one('master.shift', string='Shift', store=True, required=False, domain="[('kontraktor_id', '=', kontraktor_barging_id)]")
    # New Shift
    shift_mode_id = fields.Many2one('master.shiftmode', string='Shift', related='kontraktor_barging_id.shift_mode_id')
    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift', required=True, domain="[('shift_mode_id', '=', shift_mode_id)]")
    # ==========
    basis = fields.Selection([
        ('ritase', 'Ritase'),
        ('timbangan', 'Timbangan'),
        ('survey_int', 'Survey Internal'),
    ], default='ritase', string='Basis', store=True, required=True)
    ritase = fields.Integer('Ritase', store=True)
    total_fleet = fields.Integer('Total Fleet', store=True, required=True)
    volume = fields.Float('Volume', store=True, required=True)

    carrier = fields.Selection([
        ('mv', 'MV'),
        ('barge', 'Barge'),
    ], default='mv', string="Carrier", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], string='State', default='draft', readonly=True)

    @api.constrains('source_group')
    def _check_lineup(self):
        for prod_detail in self:
            if not prod_detail.source_id:
                raise ValidationError(_("Please Input Source"))

    @api.depends('source_group', 'company_id')
    def _get_source_group(self):
        for prod_detail in self:
            group_obj = self.env['master.sourcegroup']
            if prod_detail.source_group:
                group_id = group_obj.search([('name', 'ilike', prod_detail.source_group)])
                if group_id:
                    prod_detail.source_group_id = group_id
                else:
                    prod_detail.source_group_id = False

    @api.onchange('source_group', 'company_id')
    def source_datas(self):
        if self.source_id:
            self.source_id = False

    @api.onchange('shipping_id')
    def change_value_ship(self):
        if self.shipping_id:
            shipping_id = self.shipping_id
            # Set Value
            self.mv_id = shipping_id.mv_id
            self.barge_id = shipping_id.barge_id
            self.buyer_id = shipping_id.buyer_id
            self.market_type = shipping_id.market_type
        else:
            self.mv_id = False
            self.buyer_id = False

    @api.onchange('barge_detail_id')
    def change_value_barge_lineup(self):
        if self.barge_detail_id:
            barge_detail_id = self.barge_detail_id
            # Set Value
            self.barge_id = barge_detail_id.barge_from_lineup_id
            self.jetty_id = barge_detail_id.jetty_id
        else:
            self.barge_id = False

    @api.onchange('company_id')
    def change_shipping(self):
        if self.company_id:
            self.shipping_id = False

    # Button Submit and Revice
    def action_submit(self):
        for prod_detail in self:
            if prod_detail.state == 'draft':
                prod_detail.write({
                    'state': 'complete'
                })
            return

    def action_revise(self):
        for prod_detail in self:
            if prod_detail.state == 'complete':
                prod_detail.write({
                    'state': 'draft'
                })
            return
