from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date

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


# Master Fuel Maintank
class FuelMaintank(models.Model):
    _name = "fuel.maintank"
    _description = "Fuel Maintank"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    company_id = fields.Many2one(
        'res.company',
        string='IUP', store=True, default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    code = fields.Char('Code', store=True, required=True)
    name = fields.Char('Name', required=True, store=True)
    location_id = fields.Many2one('fuel.lokasi.kerja', string='Lokasi Kerja', store=True, required=True, domain="[('state', '=', 'active')]")
    tank_capacity = fields.Float(string='Capacity', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


# Master Fuel Reporting Daily
class FuelReport(models.Model):
    _name = "fuel.report"
    _description = "Fuel Reporting"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    company_id = fields.Many2one(
        'res.company',
        string='IUP', store=True, default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    name = fields.Char('Name', compute='get_compute_name', store=True)
    maintank_id = fields.Many2one('fuel.maintank', string='Maintank', store=True, required=True, domain="[('state', '=', 'active'), ('company_id', '=', company_id)]")
    fuel_report_line_ids = fields.One2many('fuel.report.line', 'fuel_report_id', string='Report Daily', store=True)
    period_month = fields.Selection(
        selection=MONTH_SELECTION,
        string='Month',
        help='Select the desired month'
    )
    selected_years = fields.Selection(selection='_get_year_selection', string='Years')
    period_month_int = fields.Integer('Int Month', compute='_get_int_period', store=True)
    period_year_int = fields.Integer('Int Years', compute='_get_int_period', store=True)
    total_daily = fields.Float('Total Stock in Month', store=True, compute='_calc_total_line')
    last_volume = fields.Float('Stock Last Month', default=0.0, store=True)

    # ======= Constraint =========
    @api.constrains('maintank_id', 'company_id', 'period_month', 'selected_years')
    def _check_do_report(self):
        for do_report in self:
            do_report_ids = self.env['fuel.report'].search([('maintank_id', '=', do_report.maintank_id.id), ('id', '!=', do_report.id), ('company_id', '=', do_report.company_id.id), ('period_month', '=', do_report.period_month), ('selected_years', '=', do_report.selected_years)])
            if do_report_ids:
                raise ValidationError(_("DO Report already exist"))

    # ======= Function =========

    @api.depends('period_month', 'selected_years', 'maintank_id')
    def get_compute_name(self):
        for fuel_report in self:
            name_month = dict(self._fields['period_month'].selection).get(fuel_report.period_month)
            name = _("[%s] %s %s") % (fuel_report.maintank_id.name, name_month, fuel_report.selected_years)
            fuel_report.name = name or ""

    @api.depends('period_month', 'selected_years')
    def _get_int_period(self):
        for fuel_report in self:
            fuel_report.period_month_int = int(fuel_report.period_month)
            fuel_report.period_year_int = int(fuel_report.selected_years)

    @api.depends('fuel_report_line_ids', 'fuel_report_line_ids.fueling_date', 'fuel_report_line_ids.total_volume', 'last_volume')
    def _calc_total_line(self):
        for fuel_report in self:
            total_volume = (fuel_report.last_volume + sum(line.total_volume for line in fuel_report.fuel_report_line_ids)) or 0
            fuel_report.total_daily = total_volume

    @api.onchange('period_month', 'selected_years', 'fuel_report_line_ids')
    def change_last_total(self):
        for line in self.fuel_report_line_ids:
            line._get_volume_out()
        if self.period_month and self.selected_years:
            if int(self.period_month) == 1:
                fuel_report_id = self.env['fuel.report'].search([('maintank_id', '=', self.maintank_id.id), ('period_month_int', '<', 13), ('period_year_int', '<', self.selected_years)], limit=1, order='id desc')
            else:
                fuel_report_id = self.env['fuel.report'].search([('maintank_id', '=', self.maintank_id.id), ('period_month_int', '<', int(self.period_month)), ('period_year_int', '=', self.selected_years)], limit=1, order='id desc')
            self.last_volume = fuel_report_id.total_daily or 0

    def _get_year_selection(self):
        current_year = date.today().year
        year_range = [(str(year), str(year)) for year in range(current_year, current_year + 5)]
        return year_range


# Master Fuel Reporting Daily
class FuelReportLine(models.Model):
    _name = "fuel.report.line"
    _description = "Fuel Reporting Line"

    fuel_report_id = fields.Many2one('fuel.report', string='Report', store=True, ondelete='cascade')
    maintank_id = fields.Many2one('fuel.maintank', string='Mintank', related='fuel_report_id.maintank_id')
    do_number = fields.Char('DO Number', store=True)
    fueling_date = fields.Date('Date', store=True, required=True)
    volume_in = fields.Float('Volume In', compute='_calc_fuel_in', store=True)
    fuel_in_day = fields.Float('Fuel In Day', store=True, compute='_calc_fuel_in')
    fuel_in_night = fields.Float('Fuel In Night', store=True, compute='_calc_fuel_in')
    total_volume_out = fields.Float('Volume Out', compute='_get_volume_out', store=True)
    total_volume = fields.Float('Total', store=True, compute='_calc_total_volume')
    fuel_in_ids = fields.One2many('fuel.in.details', 'line_id', string='FuelIn', store=True)
    fuel_in_night_ids = fields.One2many('fuel.in.details', 'line_night_id', string='FuelIn', store=True)

    def add_volume_in_day(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({
            'create': False,
        })
        if context.get('shift') == 'Day':
            view_id = self.env.ref('mnc_fuel_management.fuel_in_data_form').id
        elif context.get('shift') == 'Night':
            context.update({
                'default_line_night_id': self.id
            })
            view_id = self.env.ref('mnc_fuel_management.fuel_in_data_night_form').id
        return {
            'name': _("Input Volume"),
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'fuel.report.line',
            'view_id': view_id,
            'context': context
        }

    @api.constrains('fuel_report_id', 'fuel_report_id.selected_years', 'fuel_report_id.period_month')
    def check_date_periode(self):
        for fuel_report_line in self:
            if fuel_report_line.fuel_report_id:
                if str(fuel_report_line.fueling_date.month) != fuel_report_line.fuel_report_id.period_month:
                    raise ValidationError(_("Please input date must be same with month and year in period"))
                if str(fuel_report_line.fueling_date.year) != fuel_report_line.fuel_report_id.selected_years:
                    raise ValidationError(_("Please input date must be same with month and year in period"))

    @api.depends('fuel_in_day', 'fuel_in_night', 'fuel_in_ids', 'fuel_in_night_ids')
    def _calc_fuel_in(self):
        for line in self:
            line.fuel_in_day = sum(fuel_in.total_volume for fuel_in in line.fuel_in_ids) or 0
            line.fuel_in_night = sum(fuel_in.total_volume for fuel_in in line.fuel_in_night_ids) or 0
            # Calc
            fuel_in_day = line.fuel_in_day or 0
            fuel_in_night = line.fuel_in_night or 0
            total = fuel_in_day + fuel_in_night
            # Set Value
            line.volume_in = total

    @api.depends('fuel_in_day', 'fuel_in_night', 'volume_in', 'total_volume_out')
    def _calc_total_volume(self):
        for line in self:
            line.total_volume = line.volume_in - line.total_volume_out


    @api.depends('fueling_date', 'fuel_report_id', 'fuel_report_id.maintank_id')
    def _get_volume_out(self):
        for line in self:
            total_volume_out = 0
            if line.fueling_date:
                distribute_ids = self.env['fuel.distribution'].search([('fulment_date', '=', line.fueling_date), ('maintank_id', '=', line.fuel_report_id.maintank_id.id)])
                total_volume_out = sum(dist_id.volume for dist_id in distribute_ids)
            line.total_volume_out = total_volume_out

    def action_open_distribute(self):
        dist_list = []
        distribute_ids = self.env['fuel.distribution'].search([('fulment_date', '=', self.fueling_date), ('maintank_id', '=', self.fuel_report_id.maintank_id.id)])
        if distribute_ids:
            dist_list = distribute_ids.ids
        return {
            'name': _("Data Distribute"),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'fuel.distribution',
            'domain': [('id', 'in', dist_list)],
            'view_id': self.env.ref('mnc_fuel_management.fuel_distribution_view_tree').id,
            'context': dict(create=False, group_by='company_fuel_id')
        }


# Master Fuel Reporting IUP
class FuelReportCompany(models.Model):
    _name = "fuel.report.company"
    _description = "Fuel Reporting Company"

    company_fuel_id = fields.Many2one('master.fuel.company', string='Kontraktor', store=True)
    total_volume_out = fields.Float('Volume Out', store=True)


class FuelInDetails(models.Model):
    _name = "fuel.in.details"
    _description = "Fuel In Details"

    def _get_shift(self):
        context = self.env.context
        shift = context.get('shift')
        if shift:
            return shift
        else:
            return False

    type_shift = fields.Selection([
        ('Day', 'Day'),
        ('Night', 'Night'),
    ], default=_get_shift, string="Shift", store=True)
    do_number = fields.Char('DO Number', store=True, required=True)
    total_volume = fields.Float("Volume", default=0, store=True)
    line_id = fields.Many2one('fuel.report.line', string="Line Report", store=True)
    line_night_id = fields.Many2one('fuel.report.line', string="Line Report", store=True)
