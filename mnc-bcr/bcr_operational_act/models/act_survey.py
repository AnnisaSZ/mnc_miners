from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

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
    ('12', 'December'),
]


class ActSurvey(models.Model):
    _name = 'act.survey'
    _description = 'Actual Survey'
    _rec_name = "kode"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    def _get_activity(self):
        production_id = self.env['master.activity'].get_activity_by_code('01-PR')
        return production_id

    active = fields.Boolean(string='Active', default=True, store=True)
    kode = fields.Char(string='Kode Survey', readonly=True, default="#")
    company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id), domain=_company_ids_domain, store=True)
    activity_id = fields.Many2one('master.activity', string='Activity', default=_get_activity, required=True)
    # sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', domain="[('activity_id', '=', activity_id)]", required=True)
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor', domain="[('is_kontraktor', '=', True), ('company_id', '=', company_id), ('kontraktor_activity_ids', '=', activity_id)]", required=True)
    time_type = fields.Selection([
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
    ], string='Type Period', default='Weekly', store=True, required=True)
    week = fields.Selection([
        ('W1', 'W1'),
        ('W2', 'W2'),
        ('W3', 'W3'),
        ('W4', 'W4'),
        ('W5', 'W5'),
    ], string='Week', store=True)
    # ======== Period ========
    period_month = fields.Selection(
        selection=MONTH_SELECTION,
        string='Month',
        help='Select the desired month',
        required=True,
        store=True
    )
    selected_years = fields.Selection(selection='_get_year_selection', string='Years', required=True)
    date_start = fields.Date(string='Date Start', store=True, required=True)
    date_end = fields.Date(string='Date End', store=True, required=True)
    pit_id = fields.Many2one('master.area', string='PIT', domain="[('bu_company_id', '=', company_id)]", required=True, store=True)
    # ======== attachment ========
    attachment = fields.Binary('Attachments', attachment=True)
    filename_attachment = fields.Char('Name Attachments', store=True)

    # ============================
    ob_survey_line_ids = fields.One2many('act.survey.line', 'ob_survey_id', string="Overburden", store=True)
    cg_survey_line_ids = fields.One2many('act.survey.line', 'cg_survey_id', string="Coal Getting", store=True)
    ch_survey_line_ids = fields.One2many('act.survey.line', 'ch_survey_id', string="Coal Hauling", store=True)

    total_volume_ob = fields.Float('Total Volume', store=True, compute='_calc_distance')
    total_distance_ob = fields.Float('Total Distance', store=True, compute='_calc_distance')

    total_volume_cg = fields.Float('Total Volume', store=True, compute='_calc_distance')
    total_distance_cg = fields.Float('Total Distance', store=True, compute='_calc_distance')

    total_volume_ch = fields.Float('Total Volume', store=True, compute='_calc_distance')
    total_distance_ch = fields.Float('Total Distance', store=True, compute='_calc_distance')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], string='State', default='draft', readonly=True)

    # ===============================================================================

    # Button Submit and Revice
    def action_submit(self):
        for act_survey in self:
            # if cek_date_lock_act("input", self.env.user.id, act_operational.date_act):
            #     raise UserError(cek_date_lock_act_message("input"))
            if not act_survey.attachment:
                raise ValidationError(_("Please Input Attachment"))
            if act_survey.state == 'draft':
                act_survey.write({
                    'state': 'complete'
                })
            return

    def action_revice(self):
        for act_survey in self:
            if act_survey.state == 'complete':
                act_survey.write({
                    'state': 'draft'
                })
        return

    @api.depends('ob_survey_line_ids.volume', 'ob_survey_line_ids.voldist', 'ch_survey_line_ids.volume', 'ch_survey_line_ids.voldist', 'cg_survey_line_ids.volume', 'cg_survey_line_ids.voldist')
    def _calc_distance(self):
        for act_survey in self:
            result_ob = 0
            result_cg = 0
            result_ch = 0
            # Set Result Volume
            total_vol_ob = sum(survey_ob.volume for survey_ob in act_survey.ob_survey_line_ids) or 0
            total_vol_cg = sum(survey_cg.volume for survey_cg in act_survey.cg_survey_line_ids) or 0
            total_vol_ch = sum(survey_ch.volume for survey_ch in act_survey.ch_survey_line_ids) or 0
            act_survey.total_volume_ob = total_vol_ob
            act_survey.total_volume_cg = total_vol_cg
            act_survey.total_volume_ch = total_vol_ch
            # Sum Distance
            total_ob = sum(survey_ob.voldist for survey_ob in act_survey.ob_survey_line_ids) or 0
            total_cg = sum(survey_cg.voldist for survey_cg in act_survey.cg_survey_line_ids) or 0
            total_ch = sum(survey_ch.voldist for survey_ch in act_survey.ch_survey_line_ids) or 0
            # Check Values and Calculate
            if total_vol_ob > 0:
                result_ob = (total_ob / total_vol_ob) or 0
            if total_vol_cg > 0:
                result_cg = (total_cg / total_vol_cg) or 0
            if total_vol_ch > 0:
                result_ch = (total_ch / total_vol_ch) or 0
            # Set Values
            act_survey.total_distance_ob = result_ob
            act_survey.total_distance_cg = result_cg
            act_survey.total_distance_ch = result_ch

    @api.onchange('pit_id')
    def change_valies_pt(self):
        # Ob
        self.ob_survey_line_ids.pit_id = self.pit_id
        # CG
        self.cg_survey_line_ids.pit_id = self.pit_id
        self.cg_survey_line_ids.seam_id = False
        # CH
        self.ch_survey_line_ids.pit_id = self.pit_id
        self.ch_survey_line_ids.seam_id = False

    def _get_year_selection(self):
        current_year = date.today().year
        year_range = [(str(year), str(year)) for year in range(current_year, current_year + 5)]
        return year_range

    @api.constrains('attachment')
    def check_attachment(self):
        for act_survey in self:
            if act_survey.attachment:
                max_size = 50 * 1024 * 1024 #max size 10MB
                tmp = act_survey.filename_attachment.split('.')
                ext = tmp[len(tmp)-1]
                if ext not in ('pdf', 'PDF', 'jpg', 'png', 'jpeg', 'JPG', 'JPEG', 'PNG'):
                    raise ValidationError(_("The file must be a PDF or Image format file"))
                if act_survey.attachment:
                    if len(act_survey.attachment) > max_size:
                        raise ValidationError(_("Size Max 5 MB"))

    def get_bisnis_unit_code(self, company_id):
        domain = [('bu_company_id', '=', company_id.id)]
        bu_id = self.env["master.bisnis.unit"].search(domain, limit=1)
        if bu_id:
            return bu_id.code
        else:
            raise UserError('Bisnis Unit harus diinput di Master Bisnis Unit !')

    @api.model
    def create(self, vals):
        res = super(ActSurvey, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('actual.survey')
        seq_code = res.get_bisnis_unit_code(res.company_id)
        seq = seq.replace('BUCODE', seq_code)
        # Replace
        res.update({"kode": seq})
        return res


class ActSurveyLine(models.Model):
    _name = 'act.survey.line'
    _description = 'Actual Survey Details'

    ob_survey_id = fields.Many2one('act.survey', string='Survey OB', store=True)
    cg_survey_id = fields.Many2one('act.survey', string='Survey CG', store=True)
    ch_survey_id = fields.Many2one('act.survey', string='Survey CH', store=True)
    ttype = fields.Selection([
        ('OB', 'OVERBURDEN'),
        ('CG', 'Coal Getting'),
        ('CH', 'Coal Hauling'),
    ], default='OB', string='Type', store=True)
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity')
    product_ids = fields.Many2many('product.product', string='Product', domain="[('sub_activity_id', '!=', False), ('sub_activity_id', '=', sub_activity_id)]")
    product_id = fields.Many2one('product.product', string='Product', domain="[('sub_activity_id', '!=', False), ('sub_activity_id.code', '=', 'PR-OB')]")
    pit_id = fields.Many2one('master.area', string='PIT', store=True)
    seam_id = fields.Many2one('master.seam', string='Seam Code', store=True, domain="[('area_id', '!=', False), ('area_id', '=', pit_id)]")
    track_count = fields.Float('Track Count', store=True, required=True)
    volume = fields.Float('Volume', store=True, required=True)
    distance = fields.Float('Distance', store=True, required=True)
    voldist = fields.Float('Voldist', store=True, compute='_calc_voldist')

    @api.depends('volume', 'distance')
    def _calc_voldist(self):
        for line in self:
            total = (line.volume * line.distance) or 0
            line.voldist = total
