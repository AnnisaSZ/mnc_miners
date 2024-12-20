from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

from odoo.addons.bcr_planning_custom_sh.models.model import cek_date_lock_act, cek_date_lock_act_message

import logging

_logger = logging.getLogger(__name__)


class ActOperational(models.Model):
    _name = 'act.operational'
    _description = 'Actual Operational'
    _rec_name = "kode"
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_activity(self):
        hauling_id = self.env['master.activity'].get_activity_by_code('01-HL')
        production_id = self.env['master.activity'].get_activity_by_code('01-PR')
        activity_list = [hauling_id, production_id]
        return [(6, 0, activity_list)]

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    def _pit_ids_domain(self):
        return [('bu_company_id', 'in', self.env.company.id)]

    active = fields.Boolean('Active', store=True, default=True)
    # Master
    kode = fields.Char(string='Kode Production', readonly=True, default="#")
    date_act = fields.Date(string='Date', required=True)

    product = fields.Many2one('product.product', string='Product', required=True, default=False)
    ritase = fields.Float('Ritase', required=True, default=0)
    volume = fields.Float('Volume', required=True, default=0)
    distance = fields.Float('Distance', required=True, default=0)
    total_unit = fields.Float('Total Unit', required=True, default=0)

    # To Set Domain
    activity_ids = fields.Many2many('master.activity', string='Activities', default=get_activity, required=True)

    company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id), domain=_company_ids_domain, store=True)
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor', required=True)
    activity_id = fields.Many2one('master.activity', string='Activity', required=True, related='sub_activity_id.activity_id')
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', required=True, domain="[('code', 'in', ['PR-OB', 'PR-CG', 'HL-RP'])]")
    is_ob = fields.Boolean('Is OB', compute='compute_get_uom', store=True)
    area_id = fields.Many2one('master.area', string='PIT', required=True, store=True, domain="[('bu_company_id', '=', company_id)]")
    # From
    from_source_group_id = fields.Many2one('master.sourcegroup', string='From Source Group', required=True, domain="[('num_sourcegroup', 'in', [1, 2])]", help="Tempat pengambilan BatuBara")
    from_source_id = fields.Many2one('master.source', string='From Source', domain="[('source_group_id', '=', from_source_group_id)]", required=True, help="Tempat pengambilan BatuBara")
    # To
    to_source_group_id = fields.Many2one('master.sourcegroup', string='To Source Group', required=True, help="Tempat pengambilan BatuBara")
    to_source_id = fields.Many2one('master.source', string='To Source', domain="[('source_group_id', '=', to_source_group_id)]", required=True, help="Tempat pengambilan BatuBara")
    seam_id = fields.Many2one('master.seam', string='Seam', required=False)
    shift_mode_id = fields.Many2one('master.shiftmode', string='Shift Mode', related='kontraktor_id.shift_mode_id')
    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift', required=True, domain="[('shift_mode_id', '=', shift_mode_id)]")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
    ], string='State', default='draft', readonly=True)
    uom_planning = fields.Selection([
        ('bcm', 'Bcm'),
        ('ton', 'Ton'),
    ], string='UoM', compute='compute_get_uom', readonly=True, store=True)

    # ========== Function ===========

    @api.depends('sub_activity_id')
    def compute_get_uom(self):
        for act_operational in self:
            if act_operational.sub_activity_id:
                if act_operational.sub_activity_id.code == 'PR-OB':
                    act_operational.is_ob = True
                    act_operational.uom_planning = 'bcm'
                else:
                    act_operational.is_ob = False
                    act_operational.uom_planning = 'ton'
            else:
                act_operational.is_ob = False
                act_operational.uom_planning = False

    @api.onchange('company_id')
    def onchange_company_id(self):
        return {'domain': {'area_id': [('bu_company_id', '=', self.company_id.id), ('bu_company_id', '!=', False)]}}

    @api.onchange('area_id')
    def onchange_seams(self):
        if self.area_id and self.seam_id:
            self.seam_id = False

    @api.onchange('company_id')
    def onchange_domain_from_group_source(self):
        if self.company_id:
            bu_id = self.env['master.bisnis.unit'].sudo().search([('bu_company_id', '=', self.company_id.id)], limit=1)
            if bu_id:
                if bu_id.is_rom:
                    return {'domain': {
                        'from_source_group_id': [('num_sourcegroup', 'in', [1])],
                        'to_source_group_id': [('num_sourcegroup', 'not in', [2])]
                        }
                    }
                # else:
                #     return {'domain': {'from_source_group_id': [('num_sourcegroup', 'in', [1, 2])]}}

    @api.onchange('from_source_group_id', 'area_id')
    def onchange_domain_from_source(self):
        if self.from_source_group_id or self.area_id:
            if self.from_source_id:
                self.from_source_id = False
            if self.from_source_group_id.name == 'PIT':
                return {'domain': {'from_source_id': [('source_group_id', '=', self.from_source_group_id.id), ('area_code', '=', self.area_id.id), ('bu_company_id', '=', self.company_id.id)]}}
            else:
                return {'domain': {'from_source_id': [('source_group_id', '=', self.from_source_group_id.id), ('bu_company_id', '=', self.company_id.id)]}}

    @api.onchange('to_source_group_id', 'area_id')
    def onchange_domain_to_source(self):
        if self.to_source_group_id or self.area_id:
            if self.to_source_id:
                self.to_source_id = False
            if self.to_source_group_id.name == 'PIT':
                return {'domain': {'to_source_id': [('source_group_id', '=', self.to_source_group_id.id), ('area_code', '=', self.area_id.id), ('bu_company_id', '=', self.company_id.id)]}}
            elif self.to_source_group_id.name == 'BARGE':
                return {'domain': {'to_source_id': [('source_group_id', '=', self.to_source_group_id.id), ('bu_company_ids', 'in', self.company_id.ids)]}}
            else:
                return {'domain': {'to_source_id': [('source_group_id', '=', self.to_source_group_id.id), ('bu_company_id', '=', self.company_id.id)]}}

    @api.onchange('sub_activity_id')
    def onchange_contractor(self):
        self.ensure_one()
        if self.sub_activity_id:
            # self.sub_activity_id = False
            self.kontraktor_id = False
            return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('kontraktor_activity_ids', '=', self.activity_id.id)]}}
        else:
            return {'domain': {'kontraktor_id': [('is_kontraktor', '=', True), ('company_id', '=', self.company_id.id), ('kontraktor_activity_ids', '!=', False)]}}

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
        res = super(ActOperational, self).create(vals)
        if cek_date_lock_act("input", self.env.user.id, res.date_act):
            raise UserError(cek_date_lock_act_message("input"))
        if res.activity_id.code == '01-HL':
            seq = self.env['ir.sequence'].next_by_code('actual.operational.hauling')
        elif res.activity_id.code == '01-PR':
            seq = self.env['ir.sequence'].next_by_code('actual.operational.production')
        seq_code = res.get_bisnis_unit_code(res.company_id)
        seq = seq.replace('BUCODE', seq_code)
        # Replace
        res.update({"kode": seq})
        return res

    # def write(self, values):
    #     res = super(ActOperational, self).write(values)
    #     print("SSSSSSSSSSSSSSSSSS")
    #     return res

    # Button Submit and Revice
    def action_submit(self):
        for act_operational in self:
            if cek_date_lock_act("input", self.env.user.id, act_operational.date_act):
                raise UserError(cek_date_lock_act_message("input"))
            # if not act_operational.attachment:
            #     raise ValidationError(_("Please Input Attachment"))
            if act_operational.state == 'draft':
                act_operational.write({
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

    @api.constrains('to_source_group_id', 'to_source_id', 'from_source_group_id', 'from_source_id')
    def _check_source_production(self):
        for act_operational in self:
            if act_operational.to_source_group_id and act_operational.to_source_id:
                if act_operational.to_source_id.source_group_id != act_operational.to_source_group_id:
                    raise ValidationError(_("To Source and To Source Group Not Same"))
            if act_operational.from_source_group_id and act_operational.from_source_id:
                if act_operational.from_source_id.source_group_id != act_operational.from_source_group_id:
                    raise ValidationError(_("From Source and From Source Group Not Same"))

    @api.constrains('shift_line_id', 'shift_mode_id')
    def _check_shift(self):
        for act_operational in self:
            if act_operational.shift_line_id.shift_mode_id != act_operational.shift_mode_id:
                raise ValidationError(_("Shift Not same in kontraktor"))

    @api.constrains('product', 'sub_activity_id')
    def _check_product(self):
        for act_operational in self:
            if act_operational.product.sub_activity_id != act_operational.sub_activity_id:
                raise ValidationError(_("Sub Activity Not same with Product"))

    @api.constrains('kontraktor_id', 'company_id')
    def _check_kontraktor(self):
        for act_operational in self:
            if act_operational.kontraktor_id.company_id != act_operational.company_id:
                raise ValidationError(_("Bisnis Unit Not same with Kontraktor"))
