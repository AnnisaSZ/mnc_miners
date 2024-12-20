from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


# FUEL TRUCK DISTRIBUTION
class FuelTruckDistribution(models.Model):
    _name = 'fuel.distribution'
    _description = 'Fuel Distribution'
    _rec_name = 'distribution_number'

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    active = fields.Boolean('Active', default=True, store=True)
    company_id = fields.Many2one(
        'res.company',
        string='IUP', store=True, default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    distribution_number = fields.Char(string='Distribution Number', size=25, store=True, required=True)
    fulment_date = fields.Date(string='Tanggal Pengisian', store=True, required=True)
    fuel_truck_id = fields.Many2one('master.fuel.unit', string='Kode Unit', store=True, required=True, domain="[('fuel_truck', '=', True), ('company_id', '=', company_id)]")
    company_fuel_id = fields.Many2one('master.fuel.company', string='Kontraktor', store=True, related='fuel_truck_id.company_fuel_id')
    maintank_id = fields.Many2one('fuel.maintank', string='Maintank', store=True, required=True)

    volume = fields.Float(string='Pengisian Ulang', size=25, store=True, required=True)
    driver_id = fields.Many2one('master.fuel.driver', string='Driver/Operator', store=True, required=True, domain="[('company_fuel_id', '=', company_fuel_id), ('company_id', '=', company_id)]")
    attachment = fields.Binary(string='Distribution Form', store=True)
    attachment_filename = fields.Char(string='Filename', size=25, store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], default='draft', store=True, required=True)
    # ===================
    total_consume_volume = fields.Float('Distribute Volume', compute='_count_fuel', store=True)
    # ===================
    distribution_line_ids = fields.One2many('fuel.distribution.line', 'distribute_id', string='Distribution Unit', store=True)

    # ===================
    # distance_volume = fields.Float('Distance Volume', store=True, compute='_count_fuel')
    # fulment_time_in = fields.Float(string='Waktu Pengisian In', store=True, required=True)
    # fulment_time_out = fields.Float(string='Waktu Pengisian Out', store=True, required=True)
    # shift = fields.Selection([
    #     ('day', 'Day'),
    #     ('night', 'Night'),
    # ], default='day', store=True, required=True)
    # flow_start = fields.Float(string='Flow Meter Awal', size=25, store=True, required=True)
    # flow_end = fields.Float(string='Flow Meter Akhir', size=25, store=True, required=True)
    # fuelman_id = fields.Many2one('master.fuel.fuelman', string='Fuelman', store=True, required=True)
    # foreman_id = fields.Many2one('master.fuel.foreman', string='Foreman', store=True, required=True)
    # user_eng_id = fields.Many2one('master.fuel.user', string='Engineering Opr', store=True, required=True)
    # user_pjo_id = fields.Many2one('master.fuel.user', string='PJO', store=True, required=True)

    @api.depends('distribution_line_ids', 'distribution_line_ids.total_liter')
    def _count_fuel(self):
        for distribute in self:
            total_fuel = sum(line.total_liter for line in distribute.distribution_line_ids) or 0
            distance_fuel = distribute.volume - total_fuel
            distribute.total_consume_volume = total_fuel

    def action_submit(self):
        self.ensure_one()
        if not self.attachment:
            raise ValidationError(_("Please Input attachment"))
        self.update({
            'state': 'complete'
        })
        return

    def action_set_draft(self):
        self.ensure_one()
        self.update({
            'state': 'draft'
        })
        return

    @api.constrains('distribution_number', 'company_id')
    def _check_distribution_number(self):
        for distribute in self:
            distribute_ids = self.env['fuel.distribution'].search([('distribution_number', '=', distribute.distribution_number), ('id', '!=', distribute.id), ('company_id', '=', distribute.company_id.id)])
            if distribute_ids:
                raise ValidationError(_("Distribution Number must be unique"))


class FuelTruckDistributionLine(models.Model):
    _name = 'fuel.distribution.line'
    _description = 'Fule Dist Line'
    _rec_name = 'unit_id'
    _order = 'distribute_date asc, shift_time asc'


    active = fields.Boolean('Active', default=True, store=True)
    distribute_id = fields.Many2one('fuel.distribution', string='Distribution Number', store=True, ondelete='cascade')
    distribute_date = fields.Date(string='Tanggal Pengisian', store=True, related="distribute_id.fulment_date")
    company_id = fields.Many2one('res.company', string='IUP', store=True, related='distribute_id.company_id')
    shift_time = fields.Float(string='Jam', size=25, store=True, required=True, group_operator=False)
    unit_id = fields.Many2one('master.fuel.unit', string='Kode Unit', store=True, required=True, domain="[('company_id', '=', company_id)]")
    jenis_unit_id = fields.Many2one('master.jenis.unit', string='Jenis Unit', store=True, related='unit_id.jenis_unit_id')
    company_unit_id = fields.Many2one('master.fuel.company', string='Kontraktor', store=True, related='unit_id.company_fuel_id')
    next_id = fields.Char( string="Next ID")
    hm = fields.Float('HM Akhir', store=True, group_operator=False)
    hm_awal = fields.Float('HM Awal', compute="_compute_hm_awal", store=True)
    hm_finals = fields.Float('HM', compute="_compute_hm_final", store=True)
    hm_km = fields.Float('KM', store=True, group_operator=False)
    total_liter = fields.Float('Volume', store=True, required=True)
    is_hm = fields.Boolean('Is HM', related='unit_id.is_hm', store=True)
    is_km = fields.Boolean('Is KM', related='unit_id.is_km', store=True)
    driver_id = fields.Many2one('master.fuel.driver', string='Driver/Operator', store=True, required=True)
    location_id = fields.Many2one('fuel.lokasi.kerja', string='Lokasi Kerja', store=True, required=True, domain="[('state', '=', 'active')]")
    other_info = fields.Char("Keterangan", store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], store=True, related="distribute_id.state")
    # Calculate
    new_total_ltr = fields.Float('Liter/Jam', compute='_new_calc_total_liter_hours', group_operator=False)
    new_total_ltr_km = fields.Float('Liter/Km', compute='_new_calc_total_liter_hours', group_operator=False)

    # Revisi CR Fuel Management 08/production/II/IV/2024
    # total_ltr = fields.Float('Liter/Jam', compute='_calc_total_liter_hours', store=True, group_operator=False)
    # total_ltr_km = fields.Float('Liter/Km', compute='_calc_total_liter_hours', store=True, group_operator=False)

    def action_update_data(self):
        self._new_calc_total_liter_hours()
        self._compute_hm_awal()
        self._compute_hm_final()
        return

    @api.depends('hm', 'distribute_date')
    def _compute_hm_awal(self):
        for line in self:
            # Check Shift time
            prev_line = self.env['fuel.distribution.line'].search([('distribute_date','=',line.distribute_date),('shift_time','<=',line.shift_time), ('unit_id', '=', line.unit_id.id), ('company_id','=',line.company_id.id), ('id', '<', line.id)], limit=1, order='shift_time desc, id desc')
            # Check distribute date
            if not prev_line:
                prev_line = self.env['fuel.distribution.line'].search([('distribute_date','<',line.distribute_date), ('unit_id', '=', line.unit_id.id), ('company_id','=',line.company_id.id), ('id', '<', line.id)], limit=1, order='distribute_date desc, shift_time desc, id desc')
            if line.hm:
                hm_awal = 0
                if prev_line:
                    hm_awal=prev_line.hm
                    line.hm_awal = hm_awal
                    line.next_id = prev_line.id
                line.hm_finals = line.hm - line.hm_awal
            if not line.hm_awal:
                line.hm_awal = 0
                line.hm_finals = 0
        return

    @api.depends('hm_awal')
    def _compute_hm_final(self):
        for rec in self:
            if rec.hm_awal:
                rec.hm_finals = rec.hm - rec.hm_awal
            else:
                rec.hm_finals = 0.0

    @api.depends('distribute_id', 'state', 'unit_id')
    def _new_calc_total_liter_hours(self):
        for line in self:
            line.new_total_ltr = 0
            line.new_total_ltr_km = 0
            total = 0
            if line.is_hm:
                if line.hm_finals:
                    total = line.total_liter / line.hm_finals
                line.new_total_ltr = total
            # KM
            total = 0
            if line.is_km:
                if line.hm_km:
                    total = line.total_liter / line.hm_km
                line.new_total_ltr_km = total

    @api.model 
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if 'hm_awal' in fields:
            fields.remove('hm_awal')
        res = super(FuelTruckDistributionLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'new_total_ltr' in fields or 'sum_ltr_km' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    sum_ltr = 0.0
                    sum_ltr_km = 0.0
                    sum_vol = 0.0
                    sum_hm = 0.0
                    for record in lines:
                        sum_ltr += record.new_total_ltr
                        sum_ltr_km += record.new_total_ltr_km
                        sum_vol += record.total_liter
                        sum_hm += record.hm_finals
                    if sum_vol and sum_hm:
                        sum_ltr = sum_vol/sum_hm
                    line['new_total_ltr'] = sum_ltr
                    line['new_total_ltr_km'] = sum_ltr_km
        return res

    # Revisi CR Fuel Management 08/production/II/IV/2024
    # @api.depends('distribute_id', 'state', 'unit_id')
    # def _calc_total_liter_hours(self):
    #     for line in self:
    #         line.total_ltr = 0
    #         line.total_ltr_km = 0
    #         total = 0
    #         fuel_total_ids = self.env['fuel.distribution.line'].search([('unit_id', '=', line.unit_id.id), ('id', '<=', line.id)])
    #         total_volume = sum(line.total_liter for line in fuel_total_ids)
    #         if line.is_hm:
    #             total = line.search_and_result('is_hm', total_volume)
    #             # Set Value
    #             if total > 0:
    #                 line.total_ltr = total
    #         # KM
    #         if line.is_km:
    #             result_km = line.search_and_result('is_km', total_volume)
    #             # Set Value
    #             if result_km > 0:
    #                 line.total_ltr_km = result_km

    # Revisi CR Fuel Management 08/production/II/IV/2024
    # def search_and_result(self, type_unit, total_volume):
    #     total_ltr = []
    #     total = 0
    #     domain = [('unit_id', '=', self.unit_id.id), ('id', '<=', self.id), (type_unit, '=', True)]
    #     fuel_line_ids = self.env['fuel.distribution.line'].search([('unit_id', '=', self.unit_id.id), ('id', '<=', self.id), (type_unit, '=', True)], order='id asc')
    #     for line in fuel_line_ids:
    #         if type_unit == 'is_hm':
    #             total_ltr.append(line.hm_final)
    #         else:
    #             total_ltr.append(line.hm_km)
    #     min_total = min(total_ltr) or 0
    #     max_total = max(total_ltr) or 0
    #     diff_total = (max_total - min_total) or 0
    #     if diff_total:
    #         total = total_volume / diff_total
    #     return total

    @api.constrains('shift_time')
    def _check_shift_time(self):
        for dist_line in self:
            if dist_line.shift_time < 0 or dist_line.shift_time > 24:
                raise ValidationError(_("Jam harus diisi dalam range waktu 00:00 - 23:59"))
