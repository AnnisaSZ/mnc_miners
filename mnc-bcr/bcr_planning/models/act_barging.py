from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class ActBarging(models.Model):
    _name = 'act.barging'
    _description = 'Barging'
    _rec_name = "kode"

    MARKET_LIST =[
        ('domestic', 'Domestic Market'),
        ('export', 'Export Market'),
    ]
    STATUS_SHIPPER_LIST=[
        ('on_progress', 'On Progress'),
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ]

    # KONTRAKTOR_MINING_LIST=[
    #     ('1', 'Kontraktor Mining 1'),
    #     ('2', 'Kontraktor Mining 2'),
    # ]

    # Master
    kode = fields.Char(string='Kode Barging', readonly=True, default="#")
    activity_id = fields.Many2one('master.activity', string='Activity', required=True,
                                  default=lambda self: (self.env["master.activity"].get_activity_by_code('01-BG')), help="Aktifitas di dalam produksi (Barging)")
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', required=True, help="sub dari aktifitas yang dilakukan")
    bisnis_unit_id = fields.Many2one('master.bisnis.unit',
                                     default=lambda self: (self.env["res.users"].get_default_bisnis_unit_id()), help="Hasil dari sub activity sebelumnya")
    product = fields.Many2one('product.product', string='Product', required=True, default=False)
    ritase = fields.Float('Ritase', required=True, default=0, help="Total Ritase Kendaraan")
    volume = fields.Float('Volume', required=True, default=0, help="Total Volume Produksi atas aktifitas yang dilakukan sebelumnya")
    total_unit = fields.Float('Total Unit', required=True, default=0)

    date_act = fields.Date(string='Date')
    area_id = fields.Many2one('master.area', string='Area', required=True, help="Nama Area tambang")
    stowage = fields.Float('Stowage', required=True, default=0, help="Perkiraan volume yang dimuat oleh tongkang")
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor', required=True, help="kontraktor yang melakukan aktifitas barging")
    source_id = fields.Many2one('master.source', string='Source', required=True, help="Tempat pengambilan BatuBara")
    shift_id = fields.Many2one('master.shift', string='Shift', required=True, help="Pembagian Waktu Kerja")

    barge_id = fields.Many2one('master.barge', string='Barge Name', required=True, help="Nama Kapal Tongkang")
    tugboat_id = fields.Many2one('master.tugboat', string='TugBoat Name', required=True, help="Nama kapal kecil ke Tongkang")
    market = fields.Selection(selection=MARKET_LIST, string='Market', default='domestic', required=True)
    mv_boat_id = fields.Many2one('master.mv', string='Mother Vessel', help="Mother Vessel adalah tongkang dengan muatan lbh besar")
    jetty_id = fields.Many2one('master.jetty', string='Jetty', required=True, help="Dermaga")

    seq_barge = fields.Float('Seq Barge', required=True, default=0, help="Urutan masuk Kapal Tongkang, dilihat dari barge,tugboat, & MV +1")
    lot = fields.Char('LOT', help="proses muatan kapal tongkang ke MV")

    commance = fields.Date(string='Commance', help="Tanggal dan Jam Mulai Muatan")
    complete = fields.Date(string='Complete', help="Tanggal dan Jam Muatan Selesai")

    buyer_id = fields.Many2one('res.partner', string='Buyer', required=True, help="Nama Pembeli Batubara")
    basis = fields.Float('Basis', required=True, default=0, help="Satuan (Ritase/DSR)")
    # kontraktor_mining = fields.Selection(selection=KONTRAKTOR_MINING_LIST, string='Kontraktor Mining', default='1', required=True)
    status_shipper = fields.Selection(selection=STATUS_SHIPPER_LIST, string='Status Shipper', default='1', required=True)
    remarks = fields.Text(string='Remarks', help="Keterangan delay atas activity sebelumnya")

    # <field name = "seq_barge" widget = "numeric_step" options = "{'step': 1.00, 'min': 0, 'max': 100}" />

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

    validation_plan = fields.One2many('validation.plan', 'validation_act_barging_id', string='Validation',
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

    # create, sequence
    @api.model
    def create(self, vals):
        res = super(ActBarging, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('act.barging')
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
                raise UserError('Validation untuk Form Barging belum disetting')

            ####
            result = vals
        return result

    @api.onchange('bisnis_unit_id')
    def _onchange_bisnis_unit_id(self):
        if self.bisnis_unit_id:
            self.set_validation()

    @api.onchange('sub_activity_id')
    def _onchange_sub_activity_id(self):
        if self.sub_activity_id:
            self.product = False

    @api.constrains('date_act')
    def _check_date_backdate(self):
        for record in self:
            d1 = datetime.strptime(str(record.date_act), '%Y-%m-%d')

            d4 = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
            d5 = d1 - d4
            d5 = str(d5.days + 1)
            # if int(d5) <= -1:
            #     raise ValidationError('Check Again ! Start date cannot be less than today\nYou may input backdate transaction 1 day before today')

