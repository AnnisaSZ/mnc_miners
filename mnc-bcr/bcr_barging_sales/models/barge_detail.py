from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date

import logging

_logger = logging.getLogger(__name__)

ROMAN_NUMBER = {
    '1': 'I',
    '2': 'II',
    '3': 'III',
    '4': 'IV',
    '5': 'V',
    '6': 'VI',
    '7': 'VII',
    '8': 'VIII',
    '9': 'IX',
    '10': 'X',
    '11': 'XI',
    '12': 'XII',
}


class SalesShipping(models.Model):
    _name = "barge.detail"
    _description = 'Barge Detail'
    _rec_name = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean('Active', store=True, default=True)
    # Shipping
    shipping_id = fields.Many2one('sales.shipping', 'Shipping', required=True, store=True)
    contract_id = fields.Many2one('buyer.contract', 'Contract', related='shipping_id.contract_id', store=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Bisnis Unit', store=True, related='shipping_id.contract_id.company_id', ondelete='cascade')
    mv_id = fields.Many2one('master.mv', string='MV Name', store=True)
    barge_id = fields.Many2one('master.barge', string='Barge Name', store=True)
    buyer_id = fields.Many2one('res.partner', string="Buyer", store=True, required=True, domain="[('is_buyer', '=', True)]")
    market_type = fields.Selection([
        ('export', 'Export'),
        ('domestic', 'Domestic'),
    ], default='export', string='Market', store=True, required=True, tracking=True)
    # Destination
    dest_country_id = fields.Many2one('res.country', string="Destination Country", store=True)
    dest_local = fields.Char('Destination Local', store=True)
    # Carrier
    carrier = fields.Selection([
        ('mv', 'MV'),
        ('barge', 'Barge'),
    ], default='mv', string="Carrier", store=True)
    # no_barge = fields.Integer('No. Barge', store=True)

    # Barge Lineup
    barge_lineup_id = fields.Many2one('barge.lineup', 'Barge Lineup', store=True, domain="[('shipping_id', '=', shipping_id), ('total_barge_detail', '=', 0)]")
    barge_from_lineup_id = fields.Many2one('master.barge', string='Barge Name', store=True, required=True)
    tugboat_id = fields.Many2one('master.tugboat', string="Tugboat", store=True, required=True)
    #
    sizing = fields.Selection([
        ('sizing', 'Sizing'),
        ('no_sizing', 'No Sizing'),
    ], default='sizing', string='Sizing', store=True, required=True)
    jetty_id = fields.Many2one('master.jetty', string='Jetty Name', required=True, store=True)
    laycan_start = fields.Date('Laycan Start', store=True, required=True)
    laycan_end = fields.Date('Laycan End', store=True, required=True)
    calory_id = fields.Many2one('master.calory', string='Calory', store=True, required=True)
    provisional_quantity = fields.Float('Provisional Qty', required=True, store=True)
    status_jetty = fields.Selection([
        ('waiting_barge', 'Waiting barge'),
        ('otw_jetty', 'OTW Jetty'),
        ('tambat', 'Tambat(Queue)'),
        ('process_loading', 'Process Loading'),
        ('process_vessel', 'Process Vessel'),
        ('complete', 'Complete'),
    ], default='waiting_barge', string='Status Jetty', store=True, tracking=True)
    status_anchorage = fields.Selection([
        ('waiting_barge', 'Waiting barge'),
        ('tambat', 'Tambat(Queue)'),
        ('process_loading', 'Process Loading'),
        ('process_vessel', 'Process Vessel'),
        ('complete', 'Complete'),
        ('clearence', 'Clearence Doc'),
        ('sail_out', 'Sail Out'),
    ], default='waiting_barge', string='Status Anchorage', store=True, tracking=True)
    #
    initial_date = fields.Datetime('Initial Date', store=True)
    commence_date = fields.Datetime('Commence Date', store=True)
    complete_date = fields.Datetime('Complete Date', store=True)
    cast_off_date = fields.Datetime('Cast Off Date', store=True)
    # return_cargo = fields.Float('Return Cargo', store=True, required=True)
    # load_cargo = fields.Float('Load Cargo', store=True, digits="Barge Detail", required=True)
    dsr_volume_barge = fields.Float('Dsr Volume barge', compute='_calc_dsr_volume', digits="Barge Detail", store=True)
    line_ids = fields.One2many('barge.detail.line', 'barge_id',string='Barge', store=True, copy=False)

    volume_est = fields.Float('Volume Estimate', compute='_calc_volume_est', store=True)
    product_detail_ids = fields.One2many('product.detail', 'barge_detail_id', string='Product Details')
    # User Kontraktor
    kontraktor_uids = fields.Many2many('res.users', 'barge_user_rel', 'user_id', 'barge_detail_id', string="User Kontraktor", compute='_get_user_kontrakotr', store=True)
    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], string='State', default='draft', readonly=True)
    attachment = fields.Binary('Attachments', attachment=True)
    filename_attachment = fields.Char('Name Attachments', store=True)
    is_creator = fields.Boolean(string='is creator', compute='_is_creator')
    sequence_code = fields.Char(string='Doc No.')
    is_adminsite = fields.Boolean('Check', compute='_check_user_group')

    def action_archive(self):
        res = super().action_archive()
        for detail in self:
            detail.write({'barge_lineup_id': False})
        return res

    def _default_si_spk(self):
        iup_id = self.shipping_id.iup_id
        number = self.sequence_code
        no_si = self.no_si
        no_spk = self.no_spk
        if iup_id and not number and not no_si and not no_spk:
            number =  self.env['ir.sequence'].sudo().next_by_code('no.contract')
            no_si = no_spk = number
            code_month = ROMAN_NUMBER[str(datetime.now().month)]
            no_si = no_si.replace('CUSTOMCODE', 'SI/' + iup_id.code + '/' + code_month)
            no_spk = no_spk.replace('CUSTOMCODE', 'SPK/' + iup_id.code + '/' + code_month)
            self.sequence_code = number
            self.no_si = no_si
            self.no_spk = no_spk

    no_si = fields.Char(string='No. SI', default=_default_si_spk)
    no_spk = fields.Char(string='No. SPK', default=_default_si_spk, store=True)
    no_skab = fields.Char(string='No. SKAB', store=True)
    no_spb = fields.Char(string='No. SPB', store=True)

    def generate_skab_spb(self):
        for barge_detail in self:
            if barge_detail.dsr_volume_barge:
                iup_id = barge_detail.shipping_id.iup_id
                number = barge_detail.sequence_code
                no_skab = barge_detail.no_skab
                no_spb = barge_detail.no_spb
                if number:
                    no_skab = no_spb = number
                    code_month = ROMAN_NUMBER[str(datetime.now().month)]
                    no_skab = no_skab.replace('CUSTOMCODE', 'SKAB/' + iup_id.code + '/' + code_month )
                    no_spb = no_spb.replace('CUSTOMCODE', 'SPB/' + iup_id.code + '/' + code_month )

                barge_detail.write({
                    'sequence_code':number,
                    'no_skab':no_skab,
                    'no_spb':no_spb,
                })
            else:
                raise ValidationError(_("Please fill the DSR Volume Barge!"))
        return


    def _check_user_group(self):
        self.is_adminsite = self.env.user.has_group('bcr_barging_sales.module_barge_sale_admin_site')

    def _is_creator(self):
        for barge_detail in self:
            if self.env.user.id == barge_detail.create_uid.id:
                barge_detail.is_creator = True
            else:
                barge_detail.is_creator = False

    @api.depends('line_ids', 'line_ids.pit_id')
    def _get_user_kontrakotr(self):
        for barge_detail in self:
            users = []
            for line in barge_detail.line_ids:
                partner_id = self.env['res.partner'].search([('area_ids', 'in', line.pit_id.ids), ('is_profit_sharing', '=', True)], limit=1)
                if partner_id:
                    users.append(partner_id.user_profit_id.id)
            barge_detail.kontraktor_uids = [(6, 0, users)]

    @api.depends('product_detail_ids.active', 'product_detail_ids.volume', 'product_detail_ids.state')
    def _calc_volume_est(self):
        for barge_detail in self:
            total = sum(prod_detail.volume for prod_detail in barge_detail.product_detail_ids.filtered(lambda x: x.state == 'complete' and x.active)) or 0
            barge_detail.volume_est = total

    def action_submit(self):
        for barge_detail in self:
            if not barge_detail.line_ids:
                raise ValidationError(_("Please input detail cargo"))
            cek_attch = barge_detail.line_ids.filtered(lambda x: x.attachment == False)
            if cek_attch:
                raise ValidationError(_("Please upload attachment before submit"))
            barge_detail.write({
                'state': 'complete',
            })
        return

    def action_revise(self):
        for barge_detail in self:
            if barge_detail.state == 'complete':
                barge_detail.write({
                    'state': 'draft',
                    'sequence_code': False,
                    'no_si': False,
                    'no_spk': False,
                    'no_skab': False,
                    'no_spb': False,
                })
        return

    @api.constrains('laycan_start', 'laycan_end')
    def _check_duration_laycan(self):
        for barge_detail in self:
            if barge_detail.laycan_start and barge_detail.laycan_end:
                diff_date = barge_detail.laycan_end - barge_detail.laycan_start
                if diff_date.days > 6 or diff_date.days < 2:
                    raise ValidationError(_("Laycan Date Max 7 Days or Min 3 Days Duration"))

    @api.onchange('shipping_id')
    def change_data_shipping(self):
        if self.shipping_id:
            shipping_id = self.shipping_id
            # Set Value
            self.mv_id = shipping_id.mv_id
            self.barge_id = shipping_id.barge_id
            self.buyer_id = shipping_id.contract_id.buyer_id
            self.market_type = shipping_id.market_type
            self.dest_country_id = shipping_id.dest_country_id
            self.dest_local = shipping_id.dest_local
            self.carrier = shipping_id.remark_mv
            self.laycan_start = shipping_id.laycan_start
            self.laycan_end = shipping_id.laycan_end
            self.jetty_id = False
        else:
            self.mv_id = False
            self.barge_id = False
            self.buyer_id = False
            self.dest_country_id = False
            self.laycan_start = False
            self.laycan_end = False
        self._default_si_spk()

    @api.onchange('barge_lineup_id')
    def change_data_barge_lineup(self):
        if self.barge_lineup_id:
            barge_lineup_id = self.barge_lineup_id
            # Set Value
            self.tugboat_id = barge_lineup_id.tugboat_id
            self.barge_from_lineup_id = barge_lineup_id.barge_id
            self.provisional_quantity = barge_lineup_id.provisional_quantity
        else:
            self.tugboat_id = False
            self.barge_from_lineup_id = False
            self.provisional_quantity = 0

    @api.depends('line_ids.total_cargo')
    def _calc_dsr_volume(self):
        for barge_detail in self:
            barge_detail.dsr_volume_barge = sum(line.total_cargo for line in barge_detail.line_ids)


class SalesShippingLine(models.Model):
    _name = "barge.detail.line"
    _description = 'Barge Detail Line'
    _rec_name = 'id'

    barge_id = fields.Many2one('barge.detail', string='Barge', store=True, copy=False, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Bisnis Unit', store=True, related='barge_id.contract_id.company_id', ondelete='cascade')
    company_ids = fields.Many2many('res.company', 'company_barge_line_rel', 'company_id', 'barge_line_id', related='barge_id.jetty_id.company_ids', string="Companies", store=True)
    pit_id = fields.Many2one('master.area', string="PIT", domain="[('bu_company_id', 'in', company_ids)]", store=True, copy=False, ondelete='cascade') #domain berdasarkan company
    return_cargo = fields.Float('Return Cargo', store=True, digits="Barge Detail", required=True)
    load_cargo = fields.Float('Load Cargo', store=True, digits="Barge Detail", required=True)
    total_cargo = fields.Float('Total Cargo', compute="_calc_total_cargo", store=True, digits="Barge Detail")
    attachment = fields.Binary('Attachments', attachment=True)
    filename_attachment = fields.Char('Name Attachments', store=True)

    @api.constrains('attachment')
    def check_attachment(self):
        for barge_detail in self:
            if barge_detail.attachment:
                tmp = barge_detail.filename_attachment.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF'):
                    raise ValidationError(_("The file must be a PDF format file"))

    @api.depends('return_cargo', 'load_cargo')
    def _calc_total_cargo(self):
        for barge_detail in self:
            barge_detail.total_cargo = barge_detail.return_cargo + barge_detail.load_cargo


class MasterCalory(models.Model):
    _name = "master.calory"
    _description = 'Master Calory'
    _rec_name = 'calory_name'

    active = fields.Boolean('Active', store=True, default=True)
    calory_name = fields.Char('Calory', store=True, required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Non Active'),
    ], string='Status', default='active', store=True, required=True)
