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


class ActStockOpname(models.Model):
    _name = 'act.stock.opname'
    _description = 'Actual Stock Opname'
    _rec_name = "kode"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    def _get_activity(self):
        stock_opname_id = self.env['master.activity'].get_activity_by_code('01-SR')
        return stock_opname_id

    active = fields.Boolean(string='Active', default=True, store=True)
    kode = fields.Char(string='Kode', readonly=True, default="#")
    company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id), domain=_company_ids_domain, store=True)
    activity_id = fields.Many2one('master.activity', string='Activity', default=_get_activity, required=True, store=True)
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', domain="[('activity_id', '=', activity_id), ('code', 'in', ['IN-RM', 'IN-PR'])]", required=True)
    period_month = fields.Selection(
        selection=MONTH_SELECTION,
        string='Month',
        help='Select the desired month',
        required=True,
        store=True
    )
    selected_years = fields.Selection(selection='_get_year_selection', string='Years', required=True)
    observe_date = fields.Datetime('Observe Datetime', required=True, store=True)
    # source_id = fields.Many2one('master.source', string='Source')

    so_line_ids = fields.One2many('act.stock.opname.line', 'stock_opname_id', string="SO Seams", store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], string='State', default='draft', readonly=True)
    # ======== attachment ========
    attachment = fields.Binary('Attachments', attachment=True, required=True)
    filename_attachment = fields.Char('Name Attachments', store=True)

    # ===============================================================================

    def _get_year_selection(self):
        current_year = date.today().year
        year_range = [(str(year), str(year)) for year in range(current_year, current_year + 5)]
        return year_range

    @api.onchange('sub_activity_id')
    def onchange_source_line(self):
        if self.so_line_ids:
            for line in self.so_line_ids:
                line.source_id = False

    @api.onchange('company_id')
    def onchange_sub_act(self):
        self.ensure_one()
        if self.company_id:
            self.sub_activity_id = False
            bisnis_unit_id = self.env['master.bisnis.unit'].sudo().search(
                [('bu_company_id', '=', self.company_id.id)], limit=1)
            if bisnis_unit_id:
                if bisnis_unit_id.is_rom:
                    return {'domain': {'sub_activity_id': [('activity_id', '=', self.activity_id.id), ('code', 'in', ['IN-PR'])]}}
                else:
                    return {'domain': {'sub_activity_id': [('activity_id', '=', self.activity_id.id), ('code', 'in', ['IN-RM', 'IN-PR'])]}}
            else:
                return {'domain': {'sub_activity_id': [('activity_id', '=', self.activity_id.id), ('code', 'in', ['IN-RM', 'IN-PR'])]}}
        else:
            return {'domain': {'sub_activity_id': [('activity_id', '=', self.activity_id.id), ('code', 'in', ['IN-RM', 'IN-PR'])]}}

     # Button Submit and Revice
    def action_submit(self):
        for stock_opname in self:
            # if cek_date_lock_act("input", self.env.user.id, act_operational.date_act):
            #     raise UserError(cek_date_lock_act_message("input"))
            if not stock_opname.attachment:
                raise ValidationError(_("Please Input Attachment"))
            if stock_opname.state == 'draft':
                stock_opname.write({
                    'state': 'complete'
                })
            return

    def action_revice(self):
        for act_operational in self:
            if act_operational.state == 'complete':
                act_operational.write({
                    'state': 'draft'
                })
        return

    @api.constrains('attachment')
    def check_attachment(self):
        for act_survey in self:
            if act_survey.attachment:
                max_size = 50 * 1024 * 1024 #max size 5MB
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
        res = super(ActStockOpname, self).create(vals)
        seq = self.env['ir.sequence'].next_by_code('actual.stock.opname')
        seq_code = res.get_bisnis_unit_code(res.company_id)
        seq = seq.replace('BUCODE', seq_code)
        # Replace
        res.update({"kode": seq})
        return res


class ActStockOpnameLine(models.Model):
    _name = 'act.stock.opname.line'
    _description = 'Actual Stock Opname'

    def _pit_ids_domain(self):
        return [('bu_company_id', 'in', self.env.company.id)]

    stock_opname_id = fields.Many2one('act.stock.opname', string='Stock Opname', store=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string="Bisnis Unit", related='stock_opname_id.company_id', store=True)
    pit_id = fields.Many2one('master.area', string='PIT', domain="[('bu_company_id', '=', company_id), ('bu_company_id', '!=', False)]", store=True)
    seam_id = fields.Many2one('master.seam', string='Seam Code', store=True, domain="[('area_id', '!=', False), ('area_id', '=', pit_id)]")
    # CR No. 0010/Production/XIII/VI/2024
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', related='stock_opname_id.sub_activity_id', store=True)
    source_group_id = fields.Many2one('master.sourcegroup', string='Source Group', compute='_get_source_group')
    company_group_id = fields.Many2one('res.company', string='Company', compute='_get_source_group')
    source_id = fields.Many2one('master.source', string='Source', domain="[('source_group_id', '=', source_group_id), ('bu_company_id', '=', company_group_id)]", store=True)
    # ===================================
    bedding = fields.Boolean('Bedding', store=True)
    open_stock = fields.Float('Open Stock', store=True, required=True)
    vol_in_tm = fields.Float('Vol. In Month', store=True, required=True)
    vol_out_tm = fields.Float('Vol. Out Month', store=True, required=True)
    remain_stock = fields.Float('Remain Stock', compute='_calc_remain_stock', store=True, required=False)
    stock_by_survey = fields.Float('Stock By Survey', store=True, required=True)
    vol_in_od = fields.Float('Vol. In Observer', store=True, required=True)
    vol_out_od = fields.Float('Vol. Out Observer', store=True, required=True)
    end_stock = fields.Float('End Stock By Survey', compute='_calc_end_stock', store=True, required=False)
    loses_coal = fields.Float('Loses Coal', compute='_calc_loses_coal', store=True, required=False)
    percent_loses_coal = fields.Float(" % Loses Coal", compute='_calc_loses_coal', store=True, required=False)

    @api.depends('sub_activity_id', 'stock_opname_id.sub_activity_id')
    def _get_source_group(self):
        for line in self:
            group_obj = self.env['master.sourcegroup']
            line.company_group_id = line.company_id
            if line.sub_activity_id.code == 'IN-PR':
                group_id = group_obj.search([('num_sourcegroup', '=', 3)], limit=1)
                line.source_group_id = group_id
            elif line.sub_activity_id.code == 'IN-RM':
                group_id = group_obj.search([('num_sourcegroup', '=', 2)], limit=1)
                line.source_group_id = group_id
            else:
                line.source_group_id = False

    @api.depends('open_stock', 'vol_in_tm', 'vol_out_tm')
    def _calc_remain_stock(self):
        for line in self:
            remain_stock = line.open_stock + line.vol_in_tm - line.vol_out_tm
            line.remain_stock = remain_stock or 0

    @api.depends('stock_by_survey', 'vol_in_od', 'vol_out_od')
    def _calc_end_stock(self):
        for line in self:
            end_stock = line.stock_by_survey + line.vol_in_od - line.vol_out_od
            line.end_stock = end_stock or 0

    @api.depends('end_stock', 'remain_stock', 'open_stock', 'vol_in_tm')
    def _calc_loses_coal(self):
        for line in self:
            loses = line.end_stock - line.remain_stock
            percent_loses = 0
            stock = line.open_stock + line.vol_in_tm
            if loses > 0 and stock != 0:
                percent_loses = loses / stock
            line.loses_coal = loses or 0
            line.percent_loses_coal = percent_loses

    # @api.constrains('source_id')
    # def _check_values(self):
