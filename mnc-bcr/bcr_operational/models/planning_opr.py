from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date
from itertools import groupby

import logging

_logger = logging.getLogger(__name__)

MONTH_SELECTION = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December')
]


class PlanningOperational(models.Model):
    _name = "planning.opr"
    _description = 'Planning Period'
    _rec_name = "kode_planning"

    def get_activity(self):
        hauling_id = self.env['master.activity'].get_activity_by_code('01-HL')
        production_id = self.env['master.activity'].get_activity_by_code('01-PR')
        activity_list = [hauling_id, production_id]
        return [(6, 0, activity_list)]

    active = fields.Boolean('Active', store=True, default=True)
    kode_planning = fields.Char(string='Kode Planning', readonly=True, default="#")
    company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id), store=True)
    activity_ids = fields.Many2many('master.activity', string='Activities', default=get_activity, required=True)
    activity_id = fields.Many2one('master.activity', string='Activity', required=True, domain="[('id', 'in', activity_ids)]")
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', required=True, store=True)
    option_id = fields.Many2one('planning.type.option', string='Category', store=True, required=True)
    date_start = fields.Date(string='Date Start')
    date_end = fields.Date(string='Date End')
    workdays = fields.Float('Workdays', compute='_compute_workdays', store=True)
    area_id = fields.Many2one('master.area', string='PIT', store=True)
    source_id = fields.Many2one('master.source', string='Source', help="Tempat pengambilan BatuBara")
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor', store=True)
    ts_id = fields.Many2one('ts.adb', string='TS', store=True)
    distance_plan = fields.Float('Distance Plan', default=0)
    cv_ar = fields.Float('CV GAR', default=0)
    attachment = fields.Binary('Attachments', attachment=True)
    filename_attachment = fields.Char('Name Attachments', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], string='State', default='draft', readonly=True)
    uom_planning = fields.Selection([
        ('bcm', 'Bcm'),
        ('ton', 'Ton'),
    ], string='UoM', compute='compute_get_uom', readonly=True, store=True)
    validation_plan = fields.One2many('validation.plan', 'validation_planning_period_id', string='Validation')
    revise_note = fields.Char(string='Revise Note')
    is_reviewer = fields.Boolean(string='is reviewer', compute='_set_reviewer')
    is_approver = fields.Boolean(string='is approve', compute='_set_approver')
    # Tipe Planning
    is_yearly = fields.Boolean('Yearly', store=True)
    is_monthly = fields.Boolean('Monthly', store=True)
    is_production = fields.Boolean('Is Production', compute='_get_type_activity', store=True)
    is_ob = fields.Boolean('Is Overburden', compute='compute_get_uom', store=True)

    # Monthly
    atth_monthly_id = fields.Many2one('planning.month.attachment', string='Period', domain="[('company_id', '=', company_id)]", store=True)
    attachment_plan = fields.Many2one('planning.month.attachment', string='Relation Period', related='atth_monthly_id', store=True)
    pa = fields.Float('PA', store=True)
    prodty_loader = fields.Float('Prodty Loader', store=True)
    unit_loader = fields.Integer('Unit Loader', store=True)
    breakdown_time = fields.Float('Breakdown', store=True, compute='_calculate_breakdown')

    # Lost Time
    lost_time_ids = fields.One2many('lost.time.line', 'planning_id', string='Lost Time')
    seam_plan_ids = fields.One2many('seam.code.plan.line', 'planning_id', string='Seams Plan')
    product_plan_ids = fields.One2many('seam.code.plan.line', 'planning_product_id', string='Product Plan')

    total_losttime = fields.Float('STB', compute='calculate_losttime', store=True)
    total_wh = fields.Float('WH', compute='calculate_wh', store=True)
    ua = fields.Float('UA', compute='calculate_ua', store=True)
    volume_perf_unit = fields.Float('Volume Perf. Unit', compute='calculate_volume', store=True)
    volume_total = fields.Float('Volume Total', compute='calculate_volume', store=True)
    # Adj
    adj_volume = fields.Float('Adj Volume', compute='calculate_volume', store=True)
    adj_ua = fields.Float('Adj UA', compute='calculate_volume', store=True)
    adj_wh = fields.Float('Adj WH', compute='calculate_volume', store=True)
    adj_delay = fields.Float('Adj Delay', compute='calculate_volume', store=True)
    adj_stb = fields.Float('Adj STB', compute='calculate_volume', store=True)

    # New Calc
    delay = fields.Float('Delay', store=True, compute='_calculate_delay')
    idle = fields.Float('Idle', store=True, compute='_calculate_idle')

    @api.depends('lost_time_ids', 'lost_time_ids.total_losttime', 'lost_time_ids.product_id')
    def _calculate_delay(self):
        for planning in self:
            if planning.is_monthly and planning.lost_time_ids:
                total = sum(line.total_losttime for line in planning.lost_time_ids.filtered(lambda x: x.product_id.sub_activity_id.code == 'LT-DL'))
                planning.delay = total / 60
            else:
                planning.delay = 0.0

    @api.depends('lost_time_ids')
    def _calculate_idle(self):
        for planning in self:
            if planning.is_monthly and planning.lost_time_ids:
                total = sum(line.total_losttime for line in planning.lost_time_ids.filtered(lambda x: x.product_id.sub_activity_id.code == 'LT-ID'))
                planning.idle = total
            else:
                planning.idle = 0.0

    @api.depends('pa')
    def _calculate_breakdown(self):
        for planning in self:
            bd = 24
            if planning.is_monthly and planning.pa:
                total = bd - (planning.pa / 100 * 24)
                planning.breakdown_time = total
            else:
                planning.breakdown_time = bd

    # ########################
    @api.onchange('activity_id', 'company_id', 'option_id', 'kontraktor_id')
    def change_period_monthly(self):
        self.atth_monthly_id = False
        domain = [('state', '=', 'complete'), ('activity_id', '=', self.activity_id.id), ('company_id', '=', self.company_id.id), ('option_id', '=', self.option_id.id), ('kontraktor_id', '=', self.kontraktor_id.id or False)]
        if self.is_yearly:
            domain += [('attachment_type', '=', 'Yearly')]
            return {'domain': {'atth_monthly_id': domain}}
        else:
            domain += [('attachment_type', '=', 'Monthly')]
            return {'domain': {'atth_monthly_id': domain}}

    @api.depends('idle', 'delay')
    def calculate_losttime(self):
        for planning in self:
            if planning.is_monthly:
                total = planning.idle + planning.delay
                planning.total_losttime = total
            else:
                planning.total_losttime = 0.0

    @api.depends('breakdown_time', 'total_losttime', 'pa', 'lost_time_ids', 'lost_time_ids.total_losttime', 'lost_time_ids.product_id', 'prodty_loader', 'unit_loader')
    def calculate_wh(self):
        for planning in self:
            time_wh = 24
            bd = planning.breakdown_time or 0
            stb = planning.total_losttime
            planning.total_wh = time_wh - bd - stb

    @api.depends('breakdown_time', 'total_losttime', 'pa', 'lost_time_ids', 'lost_time_ids.total_losttime', 'lost_time_ids.product_id')
    def calculate_ua(self):
        for planning in self:
            bd = planning.breakdown_time
            lost_time = planning.total_losttime
            if planning.is_monthly:
                total_wh = 24 - bd - lost_time
                if total_wh > 0:
                    planning.ua = (total_wh /(total_wh + planning.total_losttime)) * 100
            else:
                planning.ua = 0.0

    @api.depends('idle', 'ua', 'pa', 'unit_loader', 'prodty_loader', 'seam_plan_ids.volume_seam', 'product_plan_ids.volume_seam')
    def calculate_volume(self):
        for planning in self:
            volume_total = 0.0
            planning.volume_perf_unit = 0.0
            if planning.is_ob:
                volume_total = sum(line.volume_seam for line in planning.product_plan_ids) or 0.0
            else:
                volume_total = sum(line.volume_seam for line in planning.seam_plan_ids) or 0.0

            planning.volume_total = volume_total
            if planning.is_monthly:
                volume = 0.0
                adj_volume = 0.0
                if planning.ua and planning.pa and planning.unit_loader:
                    volume = (planning.ua / 100) * (planning.pa / 100) * float(planning.prodty_loader) * float(planning.unit_loader) * 24 or 0.0
                adj_volume = volume_total - volume
                # Set Value
                planning.volume_perf_unit = volume
                planning.adj_volume = adj_volume
                adj_ua = 0.0
                adj_wh = 0.0
                adj_delay = 0.0
                if planning.unit_loader and planning.prodty_loader:
                    if planning.pa:
                        adj_ua = (volume_total / (planning.pa / 100 * planning.prodty_loader * planning.unit_loader * 24)) * 100
                    adj_wh = volume_total / (float(planning.prodty_loader) * float(planning.unit_loader))
                if adj_ua and adj_wh:
                    adj_delay = (adj_wh / (adj_ua/100)) - adj_wh - planning.idle
                planning.adj_ua = adj_ua
                planning.adj_wh = adj_wh
                planning.adj_delay = adj_delay
                planning.adj_stb = adj_delay + planning.idle

    @api.onchange('volume_perf_unit', 'volume_total', 'seam_plan_ids.volume_seam', 'ua', 'pa', 'unit_loader', 'prodty_loader')
    def calculate_total_volume(self):
        if self.is_monthly:
            adj_volume = self.volume_total - self.volume_perf_unit
            self.adj_volume = adj_volume or 0.0

    def _set_approver(self):
        for rec in self:
            approver = rec.validation_plan.filtered(
                lambda x: x.user_id.id == self.env.user.id and x.validation_type_id.code == 'approve')
            if approver:
                rec.is_approver = True
            else:
                rec.is_approver = False

    def _set_reviewer(self):
        for rec in self:
            reviewer = rec.validation_plan.filtered(
                lambda x: x.user_id.id == self.env.user.id and x.validation_type_id.code == 'review')
            if reviewer:
                rec.is_reviewer = True
            else:
                rec.is_reviewer = False

    @api.depends('sub_activity_id')
    def compute_get_uom(self):
        for planning in self:
            if planning.sub_activity_id:
                if planning.sub_activity_id.code == 'PR-OB':
                    planning.is_ob = True
                    planning.uom_planning = 'bcm'
                else:
                    planning.is_ob = False
                    planning.uom_planning = 'ton'
            else:
                planning.is_ob = False
                planning.uom_planning = False

    @api.depends('activity_id')
    def _get_type_activity(self):
        for planning in self:
            if planning.activity_id:
                if planning.activity_id.code == '01-HL':
                    planning.is_production = False
                if planning.activity_id.code == '01-PR':
                    planning.is_production = True
            else:
                planning.is_production = False

    @api.onchange('activity_id')
    def onchange_contractor(self):
        self.ensure_one()
        if self.activity_id:
            self.sub_activity_id = False
            self.kontraktor_id = False
            return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('kontraktor_activity_ids', '=', self.activity_id.id)]}}
            # if self.activity_id.code == '01-HL':
            #     self.is_production = False
            #     # return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('tipe_kontraktor', '=', 'kontraktor_hauling')]}}
            #     return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('kontraktor_activity_ids', '=', self.activity_id.id)]}}
            # if self.activity_id.code == '01-PR':
            #     self.is_production = True
            #     # return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('tipe_kontraktor', '=', 'kontraktor_produksi')]}}
            #     return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('kontraktor_activity_ids', '=', self.activity_id.id)]}}
        else:
            # return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('tipe_kontraktor', '=', False)]}}
            return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('kontraktor_activity_ids', '!=', False)]}}

    @api.onchange('area_id')
    def onchange_source(self):
        if self.source_id:
            self.source_id = False

    @api.onchange('is_yearly', 'is_monthly')
    def onchange_type_planning(self):
        if self.is_yearly:
            return {'domain': {'option_id': [('period_id.name', 'ilike', 'yearly'), ('status', '=', 'active')]}}
        if self.is_monthly:
            return {
                'domain': {'option_id': [('period_id.name', 'ilike', 'monthly'), ('status', '=', 'active')]}}

    def _get_year_selection(self):
        current_year = date.today().year
        year_range = [(str(year), str(year)) for year in range(current_year, current_year + 5)]
        return year_range

    @api.depends('date_start', 'date_end')
    def _compute_workdays(self):
        if self.date_start and self.date_end:
            d1 = datetime.strptime(str(self.date_start), '%Y-%m-%d')
            d2 = datetime.strptime(str(self.date_end), '%Y-%m-%d')
            d3 = d2 - d1
            self.workdays = str(d3.days + 1)

    @api.constrains('date_start', 'date_end', 'atth_monthly_id')
    def check_date_periode(self):
        for planning in self:
            if planning.date_start.year != int(planning.atth_monthly_id.selected_years):
                if planning.is_monthly:
                    if planning.date_start < planning.atth_monthly_id.date_start:
                        raise ValidationError(_("Please input date must be same with month and year in period attachment"))
                elif planning.date_start > planning.date_end and planning.is_yearly:
                    raise ValidationError(_("Date Start must be greater than Date End"))
                else:
                    raise ValidationError(_("Please input date must be same with year in period attachment"))
            elif planning.date_start.year == int(planning.atth_monthly_id.selected_years):
                if planning.is_monthly:
                    if planning.date_start < planning.atth_monthly_id.date_start:
                        raise ValidationError(_("Please input date must be same with month and year in period attachment"))
                elif planning.is_yearly:
                    if planning.date_end.year != int(planning.atth_monthly_id.selected_years):
                        raise ValidationError(_("Please input date must be same with year in period attachment"))
                    elif planning.date_start > planning.date_end:
                        raise ValidationError(_("Date Start must be greater than Date End"))

    @api.constrains('attachment')
    def check_attachment(self):
        for planning in self:
            if planning.attachment:
                max_size = 5 * 1024 * 1024 #max size 10MB
                tmp = planning.filename_attachment.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF', 'jpg', 'png', 'jpeg', 'JPG', 'JPEG', 'PNG'):
                    raise ValidationError(_("The file must be a PDF or Image format file"))
                if planning.attachment:
                    if len(planning.attachment) > max_size:
                        raise ValidationError(_("Size Max 10 MB"))

    @api.constrains('total_wh', 'pa', 'delay', 'idle', 'breakdown_time', 'total_losttime', 'prodty_loader', 'unit_loader', 'idle', 'total_losttime', 'total_wh')
    def _check_value_perfomance(self):
        for planning in self:
            if planning.is_monthly:
                if planning.total_wh < 0 and planning.breakdown_time and planning.total_losttime:
                    raise ValidationError(_("WH must not be less than 0(Zero)"))
                if planning.pa < 0 or planning.pa > 100:
                    raise ValidationError(_("PA must be with value range 0% - 100%"))
                if planning.delay < 0:
                    raise ValidationError(_("Delay must not be less than 0(Zero)"))
                if planning.idle < 0:
                    raise ValidationError(_("Idle must not be less than 0(Zero)"))
                if planning.prodty_loader < 0:
                    raise ValidationError(_("Prodty must not be less than 0(Zero)"))
                if planning.unit_loader < 0:
                    raise ValidationError(_("N Unit must not be less than 0(Zero)"))
                if planning.delay > 24:
                    raise ValidationError(_("Delay must not be greater than 24 Hours"))
                if planning.idle > 24:
                    raise ValidationError(_("Idle must not be greater than 24 Hours"))
                if planning.breakdown_time > 24:
                    raise ValidationError(_("BD must not be greater than 24 Hours"))
                if planning.total_losttime > 24:
                    raise ValidationError(_("STB must not be greater than 24 Hours"))
                if planning.total_wh > 24:
                    raise ValidationError(_("WH must not be greater than 24 Hours"))

    @api.constrains('area_id', 'company_id', 'source_id', 'activity_id', 'sub_activity_id', 'atth_monthly_id')
    def _check_value_import(self):
        for planning in self:
            if planning.area_id.bu_company_id != planning.company_id:
                raise ValidationError(_("PIT Not in Company"))
            if planning.source_id.area_code != planning.area_id:
                raise ValidationError(_("Source Not in PIT"))
            if planning.sub_activity_id.activity_id != planning.activity_id:
                raise ValidationError(_("Sub Activity Not in Activity"))
            if planning.atth_monthly_id.state == 'draft':
                raise ValidationError(_("Attachments must be state Complete"))

    # Button Submit and Revice
    def action_submit(self):
        for planning_opr in self:
            if planning_opr.state == 'draft':
                if planning_opr.is_monthly and planning_opr.total_wh < 0:
                    raise UserError(_("WH must not be less than 0(Zero)"))
                planning_opr.write({
                    'state': 'complete'
                })
            return

    def action_revice(self):
        for planning_opr in self:
            if planning_opr.state == 'complete':
                planning_opr.write({
                    'state': 'draft'
                })
        return

    def get_bisnis_unit_code(self, company_id):
        domain = [('bu_company_id', '=', company_id.id)]
        bu_id = self.env["master.bisnis.unit"].search(domain, limit=1)
        if bu_id:
            return bu_id.code
        else:
            raise UserError('Bisnis Unit harus diinput di Master Bisnis Unit !')

    # create, sequence
    @api.model
    def create(self, vals):
        res = super(PlanningOperational, self).create(vals)
        if res.is_yearly:
            seq = self.env['ir.sequence'].next_by_code('planning.yearly')
        else:
            seq = self.env['ir.sequence'].next_by_code('planning.monthly')
        seq_code = res.get_bisnis_unit_code(res.company_id)
        # Change BUCODE
        seq = seq.replace('BUCODE', seq_code)
        # Replace
        res.update({"kode_planning": seq})
        return res


class ValidationPlan(models.Model):
    _inherit = 'validation.plan'

    validation_planning_period_id = fields.Many2one('planning.opr', string='Planning Period')


class LostTimeLines(models.Model):
    _name = 'lost.time.line'

    def _get_sub_act(self):
        lost_id = self.env['master.activity'].get_activity_by_code('01-LT')
        sub_act_list = []
        lost = self.env['master.activity'].browse(lost_id)
        for sub in lost.sub_activity_ids.filtered(lambda x: x.code in ('LT-DL', 'LT-ID')):
            sub_act_list.append(sub.id)
        return [(6, 0, sub_act_list)]

    planning_id = fields.Many2one('planning.opr', 'Planning', store=True)
    sub_activity_ids = fields.Many2many('master.sub.activity', string='Sub Activity', default=_get_sub_act)
    product_id = fields.Many2one('product.product', string='Description', required=True, domain="[('sub_activity_id', 'in', sub_activity_ids)]")
    uom_id = fields.Many2one('uom.uom', string='Unit Measure', related='product_id.uom_id')
    code = fields.Char('Code', store=True)
    total_losttime = fields.Float('Duration', required=True, store=True, default=0.0)


class SeamCodeLine(models.Model):
    _name = 'seam.code.plan.line'

    def _get_sub_act(self):
        lost_id = self.env['master.activity'].get_activity_by_code('01-LT')
        sub_act_list = []
        lost = self.env['master.activity'].browse(lost_id)
        for sub in lost.sub_activity_ids.filtered(lambda x: x.code in ('LT-DL', 'LT-ID')):
            sub_act_list.append(sub.id)
        return [(6, 0, sub_act_list)]

    sub_activity_ids = fields.Many2many('master.sub.activity', string='Sub Activity', default=_get_sub_act)
    planning_id = fields.Many2one('planning.opr', 'Planning', store=True)
    planning_product_id = fields.Many2one('planning.opr', 'Planning', store=True)
    area_id = fields.Many2one('master.area', string='PIT', related='planning_id.area_id', store=True)
    is_ob = fields.Boolean('Is Overburden', related='planning_id.is_ob', store=True)
    is_product_ob = fields.Boolean('Is Overburden', related='planning_product_id.is_ob', store=True)
    seam_id = fields.Many2one('master.seam', string='Seam Code')
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', related='planning_product_id.sub_activity_id')
    product_id = fields.Many2one('product.product', string='Material', domain="[('sub_activity_id', '=', sub_activity_id)]")
    uom_id = fields.Many2one('uom.uom', string='Unit Measure', related='product_id.uom_id')
    volume_seam = fields.Float('Volume', store=True, required=True)
    ts_id = fields.Many2one('ts.adb', string='TS', store=True)
    cv_ar = fields.Float('CV GAR', default=0)
    uom_planning = fields.Selection([
        ('bcm', 'Bcm'),
        ('ton', 'Ton'),
    ], string='UoM', related='planning_id.uom_planning', store=True)
    uom_product_planning = fields.Selection([
        ('bcm', 'Bcm'),
        ('ton', 'Ton'),
    ], string='UoM', related='planning_product_id.uom_planning', store=True)


# Period in Planning
class PlanMonthAttachment(models.Model):
    _name = "planning.month.attachment"
    _description = 'Planning Month Attachments'
    _rec_name = 'name'

    def get_activity(self):
        hauling_id = self.env['master.activity'].get_activity_by_code('01-HL')
        production_id = self.env['master.activity'].get_activity_by_code('01-PR')
        activity_list = [hauling_id, production_id]
        return [(6, 0, activity_list)]

    active = fields.Boolean('Active', store=True, default=True)
    period_month = fields.Selection(
        selection=MONTH_SELECTION,
        string='Month',
        help='Select the desired month'
    )
    selected_years = fields.Selection(selection='_get_year_selection', string='Years')
    attachment = fields.Binary('Attachments', attachment=True, required=True)
    filename_attachment = fields.Char('Name Attachments', store=True)
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor')
    is_production = fields.Boolean('Is Production', compute='_get_type_activity', store=True)
    option_id = fields.Many2one('planning.type.option', string='Type', store=True, required=True)
    activity_ids = fields.Many2many('master.activity', string='Activities(Not Show)', default=get_activity, required=True)
    activity_id = fields.Many2one('master.activity', string='Activity', required=True, domain="[('id', 'in', activity_ids)]")
    company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))
    # planning_ids = fields.Many2many('planning.opr', string='Planning Month', store=True)
    planning_monthly_ids = fields.One2many('planning.opr', 'attachment_plan', string='Detail Planning', domain=[('state','=','complete')])
    attachment_type = fields.Selection([
        ('Yearly', 'Yearly'),
        ('Monthly', 'Monthly'),
    ], string='Type Period', default='Yearly', store=True)
    date_start = fields.Date('Date Start(Not Show)', store=True, compute='get_date_start')
    name = fields.Char('Name', compute='get_compute_name', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], string='State', default='draft', readonly=True)
    # Total in Planning
    is_cg = fields.Boolean('Is CG', compute='_calc_volume', store=True)
    is_ob = fields.Boolean('Is OB', compute='_calc_volume', store=True)
    is_hl = fields.Boolean('Is HL', compute='_calc_volume', store=True)

    qty_coal_getting = fields.Float('Coal Getting', compute='_calc_volume', store=True)
    qty_ob = fields.Float('Overburden', compute='_calc_volume', store=True)
    qty_hauling = fields.Float('Hauling', compute='_calc_volume', store=True)
    # Attachment
    attachment_ids = fields.One2many(
        'planning.operational.attachment',
        'period_id',
        string='Attachment List', store=True, ondelete='cascade', copy=False
    )

    @api.depends('activity_id')
    def _get_type_activity(self):
        for attachment in self:
            if attachment.activity_id:
                if attachment.activity_id.code == '01-HL':
                    attachment.is_production = False
                if attachment.activity_id.code == '01-PR':
                    attachment.is_production = True
            else:
                attachment.is_production = False

    @api.depends('planning_monthly_ids', 'planning_monthly_ids.volume_total')
    def _calc_volume(self):
        for attachment in self:
            production_id = self.env['master.activity'].get_activity_by_code('01-PR')
            hauling_id = self.env['master.activity'].get_activity_by_code('01-HL')
            # Total
            total_cg = 0
            total_ob = 0
            total_hauling = 0
            # Flagging
            attachment.is_cg = False
            attachment.is_ob = False
            attachment.is_hl = False
            # to act production
            for sub_activity_id in self.env['master.activity'].browse(production_id).sub_activity_ids:
                if sub_activity_id.code == 'PR-OB':
                    total_ob = sum(planning.volume_total for planning in attachment.planning_monthly_ids.filtered(lambda x: x.sub_activity_id == sub_activity_id and x.state == 'complete' and x.kontraktor_id == attachment.kontraktor_id))
                if sub_activity_id.code == 'PR-CG':
                    total_cg = sum(planning.volume_total for planning in attachment.planning_monthly_ids.filtered(lambda x: x.sub_activity_id == sub_activity_id and x.state == 'complete' and x.kontraktor_id == attachment.kontraktor_id))
            # to act hauling
            for sub_activity_id in self.env['master.activity'].browse(hauling_id).sub_activity_ids:
                if sub_activity_id.code == 'HL-RP':
                    total_hauling = sum(planning.volume_total for planning in attachment.planning_monthly_ids.filtered(lambda x: x.sub_activity_id == sub_activity_id and x.state == 'complete'))
            if total_cg > 0:
                attachment.is_cg = True
            if total_ob > 0:
                attachment.is_ob = True
            if total_hauling > 0:
                attachment.is_hl = True

            attachment.qty_coal_getting = total_cg
            attachment.qty_ob = total_ob
            attachment.qty_hauling = total_hauling

    @api.depends('attachment_type', 'selected_years', 'period_month')
    def get_date_start(self):
        for attachment in self:
            if attachment.attachment_type == 'Monthly':
                if attachment.selected_years and attachment.period_month:
                    date_string = _("%s-%s-01") % (attachment.selected_years, attachment.period_month)
                    date = fields.Date.from_string(date_string)
                    attachment.date_start = date
                else:
                    attachment.date_start = fields.Date.today()
            else:
                attachment.date_start = fields.Date.today()

    @api.onchange('attachment_type')
    def onchange_type_planning(self):
        if self.attachment_type == 'Yearly':
            self.period_month = False
            return {'domain': {'option_id': [('period_id.name', 'ilike', 'yearly'), ('status', '=', 'active')]}}
        if self.attachment_type == 'Monthly':
            return {
                'domain': {'option_id': [('period_id.name', 'ilike', 'monthly'), ('status', '=', 'active')]}}

    @api.onchange('activity_id', 'selected_years', 'attachment_type')
    def onchange_contractor(self):
        if self.activity_id:
            self.option_id = False
            self.kontraktor_id = False
            return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('kontraktor_activity_ids', '=', self.activity_id.id)]}}
            # if self.activity_id.code == '01-HL':
            #     self.is_production = False
            #     return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('tipe_kontraktor', '=', 'kontraktor_hauling')]}}
            # if self.activity_id.code == '01-PR':
            #     self.is_production = True
            #     return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('tipe_kontraktor', '=', 'kontraktor_produksi')]}}
        else:
            return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('kontraktor_activity_ids', '!=', False)]}}

    @api.depends('company_id', 'kontraktor_id', 'selected_years', 'period_month', 'option_id')
    def get_compute_name(self):
        for plan_attach in self:
            bu_id = self.env['master.bisnis.unit'].search([('bu_company_id', '=', plan_attach.company_id.id)], limit=1)
            kontraktor = plan_attach.kontraktor_id.name or ""
            category = plan_attach.option_id.name or ""
            name = ""
            if plan_attach.attachment_type == 'Monthly':
                value = dict(self._fields['period_month'].selection).get(plan_attach.period_month) or "-"
                name = _("%s - %s [%s] [%s] [%s]") % (value, plan_attach.selected_years, bu_id.code, kontraktor, category)
            else:
                name = _("- %s [%s] [%s] [%s]") % (plan_attach.selected_years, bu_id.code, kontraktor, category)
            plan_attach.name = name

    def _get_year_selection(self):
        current_year = date.today().year
        year_range = [(str(year), str(year)) for year in range(current_year, current_year + 5)]
        return year_range

    @api.constrains('attachment')
    def check_attachment(self):
        for planning in self:
            if planning.attachment:
                max_size = 10 * 1024 * 1024 #max size 5MB
                tmp = planning.filename_attachment.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF', 'jpg', 'png', 'jpeg', 'JPG', 'JPEG', 'PNG'):
                    raise ValidationError(_("The file must be a PDF or Image format file"))
                if planning.attachment:
                    if len(planning.attachment) > max_size:
                        raise ValidationError(_("Size Max 5 MB"))

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        context = self.env.context
        if context.get('plan_id'):
            plan_id = self.env['planning.opr'].browse(context.get('plan_id'))
            domain = [('state', '=', 'complete'), ('activity_id', '=', context.get('activity_id')), ('company_id', '=', plan_id.company_id.id), ('option_id', '=', context.get('category_id')), ('kontraktor_id', '=', context.get('kontraktor_id'))]
            if plan_id.is_yearly:
                domain += [('attachment_type', '=', 'Yearly')]
            else:
                domain += [('attachment_type', '=', 'Monthly')]
        else:
            domain += [('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()

    # Button Submit and Revice
    def action_submit(self):
        for planning_opr in self:
            if planning_opr.state == 'draft':
                planning_opr.write({
                    'state': 'complete'
                })
            return

    def action_revice(self):
        for planning_opr in self:
            if planning_opr.state == 'complete':
                planning_opr.write({
                    'state': 'draft'
                })
            return

    def name_get(self):
        result = []
        for period in self:
            name = ""
            if period.attachment_type == 'Monthly':
                value = dict(self._fields['period_month'].selection).get(period.period_month) or "-"
                name = _("%s - %s") % (value, period.selected_years)
            else:
                name = _("%s") % (period.selected_years)
            result.append((period.id, name))
        return result


class PlanningOperationalAttach(models.Model):
    _name = 'planning.operational.attachment'
    _description = 'Planning Operational Attachment'
    _order = 'id asc'
    _rec_name = 'period_id'

    period_id = fields.Many2one('planning.month.attachment', string='Period', ondelete='cascade')
    name = fields.Char("Name")
    attach_file = fields.Binary(string="Attachment")
    attach_name = fields.Char(string="Attachment Name")
