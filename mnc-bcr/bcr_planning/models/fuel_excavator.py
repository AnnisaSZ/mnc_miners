from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class FuelExcavator(models.Model):
    _name = 'fuel.excavator'
    _description = 'Fuel Excavator'
    _rec_name = "kode"

    kode = fields.Char(string='Kode', readonly=True, default="#")
    date_act = fields.Date(string='Date')
    shift_id = fields.Many2one('master.shift', string="Shift", help="Pembagian Waktu Kerja")
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor', help="kontraktor yang melakukan aktifitas")

    activity_id = fields.Many2one('master.activity', string='Activity', required=True,
                                  default=lambda self: (self.env["master.activity"].get_activity_by_code('01-FL')), help="Aktifitas di dalam produksi (Barging)")
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', required=True, help="sub dari aktifitas yang dilakukan")
    bisnis_unit_id = fields.Many2one('master.bisnis.unit',
                                     default=lambda self: (self.env["res.users"].get_default_bisnis_unit_id()), help="Hasil dari sub activity sebelumnya")
    area_id = fields.Many2one('master.area', string='Area', required=True)

    unit_id = fields.Many2one('master.unit.kendaraan', string="Unit Kendaraan", required=True, help="Kode Unit Kendaraan, (EXC = EXCAVATOR, DT = Dump Truck)")
    tipe_unit_id = fields.Many2one('tipe.unit.kendaraan', string="Tipe Unit Kendaraan", required=True)
    source_id = fields.Many2one('master.source', string="Source", help="Nomor lapisan batubara di bawah permukaan tanah")

    hm_awal = fields.Float(string='HM Awal', required=True, help="Hecto Meter Awal, konversi 1 tingkat dibawah Kilo meter, 1HM = 50mtr")
    hm_akhir = fields.Float(string='HM Akhir', required=True, help="Hecto Meter Akhir, konversi 1 tingkat dibawah Kilo meter, 1HM = 50mtr")

    total_hm = fields.Float(string="Total HM", compute='_compute_total_hm', store=True)
    fuel_consumption = fields.Float(string="Fuel Consumption", compute='_compute_fuel_consumption', store=True)
    work_hours = fields.Float(string="Work Hours", compute='_compute_work_hours', store=True)


    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('approve', 'Approve'),
        ('complete', 'Complete'),
        ('reject', 'Reject'),
    ], string='State', default='draft', readonly=True)

    # Review
    total_review = fields.Integer(string='Total Review')
    total_reviewed = fields.Integer(string='Total Reviewed')
    progress_review = fields.Char(string='Review')
    review_complete = fields.Boolean(string='Review Complete')

    # Approve
    total_approve = fields.Integer(string='Total Approve')
    total_approved = fields.Integer(string='Total Approved')
    progress_approve = fields.Char(string='Approve')
    approve_complete = fields.Boolean(string='Approve Complete')

    validation_plan = fields.One2many('validation.plan', 'validation_fuel_excavator_id', string='Validation',
                                      default=lambda self: (self.set_validation()))
    revise_note = fields.Char(string='Revise Note')

    is_reviewer = fields.Boolean(string='is reviewer', compute='_set_reviewer')
    is_approver = fields.Boolean(string='is approve', compute='_set_approver')

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

    # BUTTON start, review, approve, revise, reject
    def action_start(self):
        if not self.validation_plan:
            raise UserError('User validation belum diinput !')
        self.write({'state': 'review'})

    def action_review(self):
        for rec in self:
            rec.state = 'approve'

    def action_approve(self):
        for rec in self:
            rec.state = 'complete'

    def action_revise(self):
        for rec in self:
            if rec.revise_note:
                rec.state = 'review'
            elif rec.revise_note == False:
                raise UserError('Fill Revise Note before click Revise ')

    def action_reject(self):
        for rec in self:
            rec.state = 'reject'

    @api.depends('hm_awal', 'hm_akhir')
    def _compute_total_hm(self):
        if self.hm_awal and self.hm_akhir:
            self.total_hm = self.hm_akhir - self.hm_awal

    @api.depends('hm_awal', 'hm_akhir')
    def _compute_fuel_consumption(self):
        if self.hm_awal and self.hm_akhir:
            self.fuel_consumption = (self.hm_akhir - self.hm_awal) * 15

    @api.depends('hm_awal', 'hm_akhir')
    def _compute_work_hours(self):
        if self.hm_awal and self.hm_akhir:
            self.work_hours = self.hm_akhir - self.hm_awal

    # create, sequence
    @api.model
    def create(self, vals):
        res = super(FuelExcavator, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('fuel.excavator')
        seq_code = self.env["res.users"].get_default_bisnis_unit_seq_code()
        seq = seq.replace('BUCODE', seq_code)
        res.update({"kode": seq})
        return res

    def set_validation(self):
        result = False
        bu_id = self.env["res.users"].get_default_bisnis_unit_id()
        if bu_id:
            ####
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bisnis_unit_id', '=', bu_id)],
                                                                  limit=1)
            vals = []

            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Fuel Dump Truck belum disetting')

            ####
            result = vals
        return result

    @api.onchange('bisnis_unit_id')
    def _onchange_bisnis_unit_id(self):
        if self.bisnis_unit_id:
            self.set_validation()

    @api.constrains('date_act')
    def _check_date_backdate(self):
        for record in self:
            d1 = datetime.strptime(str(record.date_act), '%Y-%m-%d')

            d4 = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
            d5 = d1 - d4
            d5 = str(d5.days + 1)
            # if int(d5) <= -1:
            #     raise ValidationError('Check Again ! Start date cannot be less than today\nYou may input backdate transaction 1 day before today')