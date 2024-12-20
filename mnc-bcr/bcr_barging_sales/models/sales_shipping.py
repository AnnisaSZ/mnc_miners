from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date
import math

import logging

_logger = logging.getLogger(__name__)


class SalesShipping(models.Model):
    _name = "sales.shipping"
    _description = 'Shipping'
    _rec_name = "id"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    active = fields.Boolean('Active', store=True, default=True)
    sales_plan_id = fields.Many2one('sales.plan', 'Plan', store=True, domain="[('state', '=', 'approve'), ('contract_id', '!=', False)]")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], default='draft', string="State", store=True, required=True, index=True)
    attachment = fields.Binary('Attachments')
    filename_attachment = fields.Char('Name Attachments', store=True)
    # Contract
    kontraktor_uids = fields.Many2many('res.users', 'shiping_user_rel', 'user_id', 'shipping_id', string="User Kontraktor", compute='_get_user_kontrakotr', store=True)
    contract_id = fields.Many2one('buyer.contract', 'No. Contract', store=True)
    company_id = fields.Many2one('res.company', string='Bisnis Unit', store=True, related='contract_id.company_id', ondelete='cascade')
    iup_id = fields.Many2one('master.bisnis.unit', string='IUP', store=True, compute='get_iup', ondelete='cascade')
    contract_type = fields.Selection([
        ('Longterms', 'Longterms'),
        ('Spot', 'Spot'),
    ], default='Longterms', string='Contract Type', store=True, tracking=True)
    buyer_id = fields.Many2one('res.partner', string="Buyer", store=True, domain="[('is_buyer', '=', True)]", tracking=True)
    term_payment_id = fields.Many2one('buyer.term', string="Terms of Payments", store=True, domain="[('status', '=', 'active')]", tracking=True)
    qty_outstanding = fields.Integer('Outstanding', compute='_calc_qty_outstanding', store=True)
    market_type = fields.Selection([
        ('export', 'Export'),
        ('domestic', 'Domestic'),
    ], default='export', string='Market', store=True, tracking=True)
    dest_country_id = fields.Many2one('res.country', string="Destination Country", store=True)
    dest_local = fields.Char('Destination Local', store=True)
    # Estimate
    product_id = fields.Many2one('product.template', string="Product", store=True, domain="[('is_marketing', '=', True)]")
    stowage_plan = fields.Float('Stowage', store=True)
    loading_rate = fields.Float('Loading Rate', store=True)
    despatch_demurrage_rate = fields.Float('Despatch Demurage Rate', store=True)
    time_allow = fields.Char('Time Allow', compute='_calculate_time', store=True)
    coal_price_contract = fields.Float('Coal Price Contract', store=True, required=True)
    laycan_start = fields.Date('Laycan Start', store=True, tracking=True)
    laycan_end = fields.Date('Laycan End', store=True, tracking=True)
    laytime_contract = fields.Integer('Laytime Contract', compute='_compute_laytime_contract', store=True)
    # Mother Vessel
    remark_mv = fields.Selection([
        ('mv', 'MV'),
        ('barge', 'Barge'),
    ], default='mv', string="Carrier", store=True)
    mv_id = fields.Many2one('master.mv', string='MV Name', store=True)
    barge_id = fields.Many2one('master.barge', string='Barge Name', store=True)
    # Actual
    arrival_time = fields.Datetime('Arrival Time', store=True)
    start_loading = fields.Datetime('Start Loading', store=True)
    complete_loading = fields.Datetime('Complete Loading', store=True)
    laytime_actual = fields.Char('Laytime Actual', store=True, compute='_calc_laytime_act')
    laytime_save = fields.Float('Laytime Saving', store=True)
    laytime_save_days = fields.Integer('Laytime Saving Days', store=True)
    laytime_save_hours = fields.Integer('Laytime Saving Hours', store=True)
    laytime_save_minutes = fields.Integer('Laytime Saving Minutes', store=True)
    dsr_volume_mv = fields.Float('Volume By DSR', compute='_calc_dsr_volume', store=True)
    dsr_date = fields.Date('DSR Date', store=True)
    coa_date = fields.Date('COA Date', store=True)
    cv_gar = fields.Float('CV GAR', store=True)
    cv_adb = fields.Float('CV ADB', store=True)
    ts = fields.Float('TS', store=True)
    ash_adb = fields.Float('ASH ADB', store=True)
    tm_ar = fields.Float('TM AR', store=True)
    dsr_total = fields.Float('DSR Total', store=True)
    coal_price_act = fields.Float('Price Coal Act', store=True)
    demurrage_claim = fields.Float('Demurage Claim', compute='_calc_demurage_claim', store=True, help="Formula -> ((arrival time + laytime actual) – (arrival time + time allow)) x rate")
    losses_cargo = fields.Float('Losses Cargo', compute='_calc_total_deadfright', store=True)
    deadfreight = fields.Float('Deadfreight', store=True)
    # Actual / Auto
    qty_limit = fields.Integer('Qty Limit', default=0, store=True)
    total_deadfreight = fields.Float('Total Deadfreight', compute='_calc_total_deadfright', store=True)
    # Barge Lineup
    barge_lineup_ids = fields.One2many('barge.lineup', 'shipping_id', string='Barge Lineup', index=True)
    barge_detail_ids = fields.One2many('barge.detail', 'shipping_id', string='Barge Details')
    plan_attach_ids = fields.One2many('sales.shipping.attachment', 'shipping_id', string='Attachment')
    # Currency
    currency_id = fields.Many2one(
        'res.currency', string='Currency', compute='_get_currency')

    uom_shipping = fields.Selection([
        ('Ton', 'Ton'),
    ], default='Ton', string='UoM')
    uom_shipping_curr = fields.Selection([
        ('Ton', '/Ton'),
    ], default='Ton', string='UoM')
    is_creator = fields.Boolean(string='is creator', compute='_is_creator')
    goods_desc = fields.Char(string='Goods Description')
    add_doc = fields.Text(string='Additional Document')

    def _is_creator(self):
        for shiping in self:
            if self.env.user.id == shiping.create_uid.id:
                shiping.is_creator = True
            else:
                shiping.is_creator = False

    def get_iup(self):
        for rec in self:
            iup = self.env['master.bisnis.unit'].search([('bu_company_id','=', rec.company_id.id)])
            rec.iup_id = iup

    @api.depends('barge_detail_ids', 'barge_detail_ids.kontraktor_uids')
    def _get_user_kontrakotr(self):
        for shiping in self:
            users = []
            for barge_detail in shiping.barge_detail_ids:
                for user_id in barge_detail.kontraktor_uids:
                    if user_id not in users:
                        users.append(user_id.id)
            shiping.kontraktor_uids = [(6, 0, users)]

    # ========== Calculate ============

    @api.depends('barge_detail_ids', 'barge_detail_ids.dsr_volume_barge', 'barge_detail_ids.state')
    def _calc_dsr_volume(self):
        for shiping in self:
            total = sum(detail.dsr_volume_barge for detail in shiping.barge_detail_ids.filtered(lambda x: x.state == 'complete')) or 0
            shiping.dsr_volume_mv = total

    @api.constrains('attachment')
    def check_attachment(self):
        for shiping in self:
            if shiping.attachment:
                tmp = shiping.filename_attachment.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF'):
                    raise ValidationError(_("The file must be a PDF format file"))

    @api.depends('market_type')
    def _get_currency(self):
        for shiping in self:
            currency_obj = self.env['res.currency']
            if shiping.market_type == 'export':
                currency_id = currency_obj.search([('name', '=', 'USD')], limit=1)
                shiping.currency_id = currency_id
            else:
                currency_id = currency_obj.search([('name', '=', 'IDR')], limit=1)
                shiping.currency_id = currency_id

    @api.depends('arrival_time', 'laytime_actual', 'time_allow', 'despatch_demurrage_rate')
    def _calc_demurage_claim(self):
        for shiping in self:
            total_demuragge_claim = 0
            shiping.demurrage_claim = total_demuragge_claim

    @api.depends('contract_id', 'contract_id.total_outstanding')
    def _calc_qty_outstanding(self):
        for shiping in self:
            total_outstanding = 0
            if shiping.contract_id:
                qty_dsr_volume = sum(barge_detail.dsr_volume_barge for barge_detail in shiping.contract_id.barge_detail_ids) or 0
                total_outstanding = shiping.contract_id.quantity - qty_dsr_volume
            shiping.qty_outstanding = total_outstanding

    @api.constrains('laycan_start', 'laycan_end')
    def _check_duration_laycan(self):
        for shiping in self:
            if shiping.laycan_start and shiping.laycan_end:
                diff_date = shiping.laycan_end - shiping.laycan_start
                if diff_date.days > 6 or diff_date.days < 2:
                    raise ValidationError(_("Laycan Date Max 7 Days or Min 3 Days Duration"))

    @api.depends('laycan_start', 'laycan_end')
    def _compute_laytime_contract(self):
        for shiping in self:
            if shiping.laycan_start and shiping.laycan_end:
                d1 = datetime.strptime(str(shiping.laycan_start), '%Y-%m-%d')
                d2 = datetime.strptime(str(shiping.laycan_end), '%Y-%m-%d')
                d3 = d2 - d1
                shiping.laytime_contract = str(d3.days + 1)

    @api.depends('stowage_plan', 'loading_rate')
    def _calculate_time(self):
        for shiping in self:
            result = "0 Days 0 Hours 0 Minutes"
            if shiping.stowage_plan and shiping.loading_rate:
                result = shiping.stowage_plan / shiping.loading_rate
                days = math.floor(result)
                hours = (result - math.floor(result)) * 24
                minutes = (hours - math.floor(hours)) * 60
                result = _("%s Days %s Hours %s Minutes") % (days, math.floor(hours), math.floor(minutes))
            shiping.time_allow = result

    @api.depends('start_loading', 'complete_loading')
    def _calc_laytime_act(self):
        for shiping in self:
            if shiping.complete_loading and shiping.start_loading:
                calc_date = shiping.complete_loading - shiping.start_loading
                shiping.laytime_actual = str(calc_date) or ""
            else:
                shiping.laytime_actual = ""

    @api.depends('currency_id', 'dsr_total', 'stowage_plan', 'deadfreight')
    def _calc_total_deadfright(self):
        for shiping in self:
            total = 0
            calc_losses = shiping.stowage_plan - shiping.dsr_total
            if calc_losses > 0:
                shiping.losses_cargo = calc_losses
                total = calc_losses * shiping.deadfreight
                if total > 0:
                    shiping.total_deadfreight = total
            elif calc_losses <= 0:
                shiping.losses_cargo = 0
            else:
                shiping.total_deadfreight = 0

    # ============ Change Data ==============
    # @api.onchange('barge_lineup_ids')
    # def change_barge_lineup_ids(self):
    #     print("XXXXXXXXXXXXXXXXXXXXXXXXX")
    #     print(self.barge_lineup_ids)
    #     vals = {}
        # self.barge_lineup_ids.create(vals)
        # self.create(vals)
        # return {'warning': {'title': _('Warning'), 'message': _("Tanggal Exp tidak boleh kurang dari tanggal reminder")}}
        # return False

    @api.onchange('sales_plan_id')
    def change_based_sales_plan(self):
        if self.sales_plan_id:
            if self.sales_plan_id.contract_id:
                self.contract_id = self.sales_plan_id.contract_id

    @api.onchange('contract_id')
    def change_contract_value(self):
        if self.contract_id:
            contract = self.contract_id
            # Set Value
            self.buyer_id = contract.buyer_id
            self.laycan_start = contract.laycan_start
            self.laycan_end = contract.laycan_end
            self.product_id = contract.product_id
            self.contract_type = contract.contract_type
            self.term_payment_id = contract.term_payment_id
            self.market_type = contract.market_type
            self.qty_limit = contract.qty_percentage

    def _check_data(self):
        if self.market_type == 'domestic':
            if not self.dest_local:
                raise ValidationError(_("Please input Dest Local"))
        elif self.market_type == 'export':
            if not self.dest_country_id:
                raise ValidationError(_("Please input Dest Country"))
        # Check Carrier
        if self.remark_mv == 'mv':
            if not self.mv_id:
                raise ValidationError(_("Please input MV Name"))
        elif self.remark_mv == 'barge':
            if not self.barge_id:
                raise ValidationError(_("Please input Barge Name"))
        # Check another value
        if not self.despatch_demurrage_rate:
            raise ValidationError(_("Please Input Despetch Demurrage Rate"))
        if not self.stowage_plan:
            raise ValidationError(_("Please Input Stowage Plan"))
        if not self.loading_rate:
            raise ValidationError(_("Please Input Loading Rate"))
        if not self.contract_type:
            raise ValidationError(_("Please Input Contract Type"))
        if not self.coal_price_contract:
            raise ValidationError(_("Please Input Coal Price Contract"))
        if not self.product_id:
            raise ValidationError(_("Please Input Product"))
        if not self.attachment:
            raise ValidationError(_("Please Input Attachments"))
        if not self.laycan_start or not self.laycan_end:
            raise ValidationError(_("Please Input Laycan Date"))
        if not self.barge_lineup_ids:
            raise ValidationError(_("Please Input Barge Lineup"))
        if not self.dsr_total:
            raise ValidationError(_("Please Input DSR Total"))
        if not self.coal_price_act:
            raise ValidationError(_("Please Input Price Coal"))

    def action_submit(self):
        if not self.contract_id:
            raise ValidationError(_("Please input Contract"))
        self._check_data()
        self.write({
            'state': 'complete'
        })
        return

    def action_revise(self):
        self.update({
            'state': 'draft',
        })
        return

    def name_get(self):
        result = []
        for shiping in self:
            carrier = ''
            if shiping.remark_mv == 'mv':
                carrier = shiping.mv_id.name
            elif shiping.remark_mv == 'barge':
                carrier = shiping.barge_id.nama_barge
            name = _("%s (%s) (%s)") % (str(shiping.id), shiping.buyer_id.name, carrier)
            result.append((shiping.id, name))
        return result

    def action_view_barge_details(self):
        result = self.env['ir.actions.act_window']._for_xml_id('bcr_barging_sales.action_barge_detail')
        # choose the view_mode accordingly
        if len(self.barge_detail_ids) > 1:
            result['domain'] = [('id', 'in', self.barge_detail_ids.ids)]
            result['context'] = {'create': 0, 'delete': 0}
        elif len(self.barge_detail_ids) == 1:
            res = self.env.ref('bcr_barging_sales.barge_detail_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = self.barge_detail_ids.id
            result['context'] = {'create': 0, 'delete': 0}
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


class BargeLineup(models.Model):
    _name = "barge.lineup"
    _description = 'Barge Lineup'
    _rec_name = 'barge_lineup_id'

    barge_lineup_id = fields.Integer('Lineup ID', store=True)
    # barge_agent = fields.Char('Barge Agent', store=True)
    barge_agent_id = fields.Many2one('barge.agent', 'Barge Agent', store=True, required=False)
    tugboat_id = fields.Many2one('master.tugboat', string='Tugboat', store=True, required=False)
    barge_id = fields.Many2one('master.barge', string='Barge Name', store=True, required=False)
    eta = fields.Date('ETA', store=True, required=False)
    consignee_id = fields.Many2one('master.consignee', 'Consignee', store=True, required=False)
    notif_party = fields.Char('Notif Party', store=True, required=False)
    surveyor_id = fields.Many2one('master.surveyor', 'Surveyor', store=True, required=False)
    laycan_start = fields.Date('Laycan Start', store=True, required=False)
    laycan_end = fields.Date('Laycan End', store=True, required=False)
    provisional_quantity = fields.Float('Provisional Qty', store=True, required=False)
    shipping_id = fields.Many2one('sales.shipping', string='Shipping', store=True)
    barge_detail_ids = fields.One2many('barge.detail', 'barge_lineup_id', string="Barge Detail", store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], string='State', related="barge_detail_ids.state")
    total_barge_detail = fields.Integer('Total Barge', store=True, compute="_get_total_barge_detail")

    @api.constrains('barge_agent_id', 'tugboat_id', 'barge_id', 'eta', 'consignee_id', 'notif_party', 'surveyor_id', 'laycan_start', 'laycan_end', 'provisional_quantity')
    def _check_lineup(self):
        for lineup in self:
            if not lineup.barge_agent_id:
                raise ValidationError(_("Please Input Barge Agent"))
            if not lineup.tugboat_id:
                raise ValidationError(_("Please Input Tugboat"))
            if not lineup.barge_id:
                raise ValidationError(_("Please Input Barge Name"))
            if not lineup.eta:
                raise ValidationError(_("Please Input ETA"))
            if not lineup.consignee_id:
                raise ValidationError(_("Please Input Consignee"))
            if not lineup.notif_party:
                raise ValidationError(_("Please Input Notif Party"))
            if not lineup.surveyor_id:
                raise ValidationError(_("Please Input Surveyor"))
            if not lineup.laycan_start:
                raise ValidationError(_("Please Input Laycan Start"))
            if not lineup.laycan_end:
                raise ValidationError(_("Please Input Laycan End"))
            if not lineup.provisional_quantity:
                raise ValidationError(_("Please Input Provisional Qty"))

    @api.depends('barge_detail_ids')
    def _get_total_barge_detail(self):
        for lineup in self:
            total = 0
            if lineup.barge_detail_ids:
                total = len(lineup.barge_detail_ids)
            lineup.total_barge_detail = total

    def create(self, vals):
        res = super(BargeLineup, self).create(vals)
        last_record = self.search([('shipping_id', '=', vals[0].get('shipping_id'))], order='barge_lineup_id desc', limit=1)
        sequence = 1
        if last_record:
            last_sequence = last_record.barge_lineup_id + 1
            sequence = last_sequence
        for res_id in res:
            res_id.update({'barge_lineup_id': sequence})
            sequence += 1
        return res

    def open_print(self):
        return {
            'name': _("Print Out Report"),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'reports.shipping.wizard',
            'view_id': self.env.ref('bcr_barging_sales.report_shipping_wizard_form').id,
            'context': {
                'default_barge_lineup_id': self.id,
            },
        }

    def check_barge_detail(self):
        for rec in self:
            barge_id = False
            for detail in rec.mapped('barge_detail_ids'):
                barge_id = detail.id
        action = {
            'name': _("Barge Detail"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'barge.detail',
            'view_id': self.env.ref('bcr_barging_sales.barge_detail_view_form').id,
        }
        if barge_id:
            action['res_id'] = barge_id
        else:
            action['context'] = {
                'default_shipping_id': rec.shipping_id.id,
                'default_barge_lineup_id': rec.id,
            }
        self.env['barge.detail']._default_si_spk()
        return action

# Master Barge
class BargeAgent(models.Model):
    _name = "barge.agent"
    _description = 'Barge Agent'

    active = fields.Boolean('Active', store=True, default=True)
    name = fields.Char('Name', required=True, store=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name != "":
            domain += [('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()


class MasterConsignee(models.Model):
    _name = "master.consignee"
    _description = 'Consignee'

    active = fields.Boolean('Active', store=True, default=True)
    name = fields.Char('Name', required=True, store=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        domain += [('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()


class MasterSurveyor(models.Model):
    _name = "master.surveyor"
    _description = 'Surveyor'

    active = fields.Boolean('Active', store=True, default=True)
    name = fields.Char('Name', required=True, store=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        domain += [('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()


class PlanningOperationalAttach(models.Model):
    _name = 'sales.shipping.attachment'
    _description = 'Shipping Attachment'
    _order = 'id asc'
    _rec_name = 'shipping_id'

    shipping_id = fields.Many2one('sales.shipping', string='Sales Plan', ondelete='cascade')
    name = fields.Char("Name")
    attach_file = fields.Binary(string="Attachment")
    attach_name = fields.Char(string="Filename")
