from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta
from odoo.http import request
import requests
import logging

_logger = logging.getLogger(__name__)


def cek_date_lock_act(tipe, myid, date_act):
    if tipe:
        if tipe == "input":
            code = "DL01"
        elif tipe == "review":
            code = "DL02"
        elif tipe == "approve":
            code = "DL03"
        else:
            return True
        date_lock_par = request.env['bcr.parameter.setting'].sudo().search(
            [("code", "=", code), ("status", "=", True)])
        print("ZZZZZZZZZZZZZZZZZZ")
        print(date_lock_par)
        if not date_lock_par:
            return False
        cek_not_allow_user_ids = date_lock_par[0].not_allow_user_ids
        if myid in cek_not_allow_user_ids.ids:
            return False
        else:
            if tipe == "input":
                h_par = date_lock_par[0].value
                date_act = datetime.strptime(str(date_act), '%Y-%m-%d')
                date_today = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
                dt = date_act - date_today
                dt = int(dt.days)
                if dt <= 0:
                    if dt < int(h_par):
                        return True
                    else:
                        return False
                elif dt > 0:
                    if dt > int(h_par):
                        return True
                    else:
                        return False
                else:
                    return True
            else:
                print("ZZZZZZZZZZZZZZZZZZ01")
                h_par = date_lock_par[0].value
                date_act = datetime.strptime(str(date_act), '%Y-%m-%d')
                date_today = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
                end_date = date_act + timedelta(days=int(h_par))
                # print(timedelta(days=int(h_par)))
                dt = end_date - date_today
                print("ZZZZZZZZZZZZZZZZZZ011")
                print("Parameter", h_par)
                print("Date Actual", date_act)
                print("Date End", end_date)
                print("Today", date_today)
                print("Total Days end - today", dt.days)
                # print(int(dt.days))
                if int(dt.days) >= 0:
                    return False
                else:
                    return True
    else:
        return True

def cek_date_lock_act_message(tipe):
    if tipe == "input":
        date_lock_par = request.env['bcr.parameter.setting'].sudo().search(
            [("code", "=", "DL01M")])
        if not date_lock_par:
            return "Not Found Message"
        return str(date_lock_par[0].value)
    elif tipe == "review":
        date_lock_par = request.env['bcr.parameter.setting'].sudo().search(
            [("code", "=", "DL02M")])
        if not date_lock_par:
            return "Not Found Message"
        return str(date_lock_par[0].value)
    elif tipe == "approve":
        date_lock_par = request.env['bcr.parameter.setting'].sudo().search(
            [("code", "=", "DL03M")])
        if not date_lock_par:
            return "Not Found Message"
        return str(date_lock_par[0].value)
    else:
        return "Not Found Message"

# planning inherit
class InheritPlanningHauling(models.Model):
    _inherit = 'planning.hauling'

    bu_company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))
    # seam_id = fields.Many2one('master.seam', string='Seam Code', required=True)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="Old Bisnis Unit")
    active = fields.Boolean(default=True)
    kontraktor_id = fields.Many2one('res.partner', string='Kontraktor', required=False)

    _sql_constraints = [
        ('positive_volume_plan', 'CHECK(volume_plan >= 0)', 'The Volume plan must be positive !')
    ]
    @api.onchange('product')
    def _onchange_bu_company_id(self):
        self.ensure_one()
        return {
            'domain':
                {
                    'kontraktor_id': [
                        ('company_id', '=', self.bu_company_id.id),
                        ('is_kontraktor', '=', True),
                        ('tipe_kontraktor', '=', 'kontraktor_hauling')
                    ]
                }
        }

    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bu_company_id', '=', bu_id)],
                                                                  limit=1)
            vals = []
            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Planning Hauling belum disetting')
            result = vals
        return result

    def action_archive(self):
        for r in self:
            if not r.user_has_groups('bcr_planning_custom_sh.group_bcr_planning_all_archive'):
                if r.state == "review":
                    raise UserError('Status data sudah Review')
                elif r.state == "complete":
                    raise UserError('Status data sudah Complete')
            res = super(InheritPlanningHauling, r).action_archive()
        return res

    def button_confirm_complete_multi(self):
        for r in self:
            r.state = 'complete'
            print(r.id, 'confirm to complete')

    def unlink(self):
        for r in self:
            if r.create_uid.id != self.env.user.id:
                raise ValidationError("Data tidak dapat di hapus")
            res = super(InheritPlanningHauling, r).unlink()
            return res

class InheritPlanningBarging(models.Model):
    _inherit = 'planning.barging'

    bu_company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="Old Bisnis Unit")
    active = fields.Boolean(default=True)
    # seam_id = fields.Many2one('master.seam', string='Seam Code', required=True)

    _sql_constraints = [
        ('positive_volume_plan', 'CHECK(volume_plan >= 0)', 'The Volume plan must be positive !')
    ]
    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bu_company_id', '=', bu_id)],
                                                                  limit=1)
            vals = []
            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Planning Barging belum disetting')
            result = vals
        return result
    def action_archive(self):
        for r in self:
            if not r.user_has_groups('bcr_planning_custom_sh.group_bcr_planning_all_archive'):
                if r.state == "review":
                    raise UserError('Status data sudah Review')
                elif r.state == "complete":
                    raise UserError('Status data sudah Complete')
            res = super(InheritPlanningBarging, r).action_archive()
        return res

    def button_confirm_complete_multi(self):
        for r in self:
            r.state = 'complete'
            print(r.id, 'confirm to complete')

    def unlink(self):
        for r in self:
            if r.create_uid.id != self.env.user.id:
                raise ValidationError("Data tidak dapat di hapus")
            res = super(InheritPlanningBarging, r).unlink()
            return res
class InheritPlanningProduction(models.Model):
    _inherit = 'planning.production'

    bu_company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))
    seam_id = fields.Many2one('master.seam', string='Seam Code', required=False)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="Old Bisnis Unit")
    active = fields.Boolean(default=True)
    status_seam = fields.Boolean(default=False)

    _sql_constraints = [
        ('positive_volume_plan', 'CHECK(volume_plan >= 0)', 'The Volume plan must be positive !')
    ]

    @api.constrains('kontraktor_id')
    def _check_kontraktor_true(self):
        for record in self:
            if not record.kontraktor_id.is_kontraktor:
                raise ValidationError('kontraktor is true not found')
    @api.onchange('area_id')
    def _onchange_bu_company_id(self):
        self.ensure_one()
        return {
            'domain':
                {
                    'kontraktor_id': [
                        ('company_id', '=', self.bu_company_id.id),
                        ('is_kontraktor', '=', True),
                        ('tipe_kontraktor', '=', 'kontraktor_produksi')
                    ]
                }
        }

    @api.onchange('sub_activity_id')
    def _onchange_sub_activity_id(self):
        for r in self:
            if r.sub_activity_id.name == "OVERBURDEN":
                r.status_seam = True
                r.seam_id = 0
            else:
                r.status_seam = False


    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bu_company_id', '=', bu_id)],
                                                                  limit=1)
            vals = []
            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Planning Production belum disetting')
            result = vals
        return result

    def action_archive(self):
        for r in self:
            if not r.user_has_groups('bcr_planning_custom_sh.group_bcr_planning_all_archive'):
                if r.state == "review":
                    raise UserError('Status data sudah Review')
                elif r.state == "complete":
                    raise UserError('Status data sudah Complete')
            res = super(InheritPlanningProduction, r).action_archive()
        return res

    def button_confirm_complete_multi(self):
        for r in self:
            r.state = 'complete'
            print(r.id, 'confirm to complete')

    def unlink(self):
        for r in self:
            if r.create_uid.id != self.env.user.id:
                raise ValidationError("Data tidak dapat di hapus")
            res = super(InheritPlanningProduction, r).unlink()
            return res
# actual inherit
class ActPlanningProduction(models.Model):
    _inherit = 'act.production'

    bu_company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))
    seam_id = fields.Many2one('master.seam', string='Seam Code', required=False)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="Old Bisnis Unit")
    active = fields.Boolean(default=True)
    status_seam = fields.Boolean(default=False)
    item_uom = fields.Many2one("uom.uom", string="Uom", compute="_get_item_uom")
    # kontraktor_id = fields.Many2one('res.partner', string='Kontraktor 2', required=True, domain="[('is_kontraktor', '=', True)]")

    @api.constrains('date_act')
    def _check_date_lock(self):
        if self.state == "draft":
            if cek_date_lock_act("input", self.env.user.id, self.date_act):
                raise UserError(cek_date_lock_act_message("input"))
        print("_check_date_lock")
    # @api.model
    # def create(self, vals):
    #     # for record in self:
    #     if cek_date_lock_act("input", self.env.user.id, vals["date_act"]):
    #         raise UserError(cek_date_lock_act_message("input"))
    #     res = super(ActPlanningProduction, self).create(vals)
    #     return res

    def action_review(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("review", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("review"))
            res = super(ActPlanningProduction, record).action_review()
            return res

    def action_approve(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("approve", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("approve"))
            res = super(ActPlanningProduction, record).action_approve()
            return res
    @api.constrains('kontraktor_id')
    def _check_kontraktor_true(self):
        for record in self:
            if not record.kontraktor_id.is_kontraktor:
                raise ValidationError('kontraktor is true not found')


    _sql_constraints = [
        ('positive_volume', 'CHECK(volume >= 0)', 'The Volume must be positive !'),
        ('positive_ritase', 'CHECK(ritase >= 0)', 'The Ritase must be positive !'),
        ('positive_total_unit', 'CHECK(total_unit >= 0)', 'The Total Unit must be positive !')
    ]

    @api.depends('product')
    def _get_item_uom(self):
        for record in self:
            record.item_uom = record.product.uom_id.id
    @api.onchange('area_id')
    def _onchange_bu_company_id(self):
        self.ensure_one()
        return {
            'domain':
                {
                    'kontraktor_id': [
                        ('company_id', '=', self.bu_company_id.id),
                        ('is_kontraktor', '=', True),
                        ('tipe_kontraktor', '=', 'kontraktor_produksi')
                    ]
                }
        }

    @api.onchange('sub_activity_id')
    def _onchange_sub_activity_id(self):
        for r in self:
            if r.sub_activity_id.name == "OVERBURDEN":
                r.status_seam = True
                r.seam_id = 0
            else:
                r.status_seam = False

    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bu_company_id', '=', bu_id)],
                                                                  limit=1)
            vals = []
            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Actual Production belum disetting')
            result = vals
        return result

    @api.constrains('date_act')
    def _check_date_backdate(self):
        print("Non Active Backdate")

    def action_archive(self):
        for r in self:
            if not r.user_has_groups('bcr_planning_custom_sh.group_bcr_planning_all_archive'):
                if r.state == "review":
                    raise UserError('Status data sudah Review')
                elif r.state == "complete":
                    raise UserError('Status data sudah Complete')
            res = super(ActPlanningProduction, r).action_archive()
        return res

    def button_confirm_complete_multi(self):
        for r in self:
            r.state = 'complete'
            print(r.id, 'confirm to complete')

    def unlink(self):
        for r in self:
            if r.create_uid.id != self.env.user.id:
                raise ValidationError("Data tidak dapat di hapus")
            res = super(ActPlanningProduction, r).unlink()
            return res


class InheritActStockroom(models.Model):
    _inherit = 'act.stockroom'

    bu_company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))
    shift_id = fields.Many2one('master.shift', string='Shift', required=False)
    seam_id = fields.Many2one('master.seam', string='Seam Code', required=True)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="Old Bisnis Unit")
    active = fields.Boolean(default=True)
    item_uom = fields.Many2one("uom.uom", string="Uom", compute="_get_item_uom")

    _sql_constraints = [
        ('positive_volume', 'CHECK(volume >= 0)', 'The Volume must be positive !')
    ]

    @api.constrains('date_act')
    def _check_date_lock(self):
        if self.state == "draft":
            if cek_date_lock_act("input", self.env.user.id, self.date_act):
                raise UserError(cek_date_lock_act_message("input"))
        print("_check_date_lock")

    # @api.model
    # def create(self, vals):
    #     # for record in self:
    #     if cek_date_lock_act("input", self.env.user.id, vals["date_act"]):
    #         raise UserError(cek_date_lock_act_message("input"))
    #     res = super(InheritActStockroom, self).create(vals)
    #     return res

    def action_review(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("review", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("review"))
            res = super(InheritActStockroom, record).action_review()
            return res

    def action_approve(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("approve", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("approve"))
            res = super(InheritActStockroom, record).action_approve()
            return res

    @api.depends('product')
    def _get_item_uom(self):
        for record in self:
            record.item_uom = record.product.uom_id.id
    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bu_company_id', '=', bu_id)],
                                                                  limit=1)
            vals = []
            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Actual Inventory belum disetting')
            result = vals
        return result

    @api.constrains('date_act')
    def _check_date_backdate(self):
        print("Non Active Backdate")

    def action_archive(self):
        for r in self:
            if not r.user_has_groups('bcr_planning_custom_sh.group_bcr_planning_all_archive'):
                if r.state == "review":
                    raise UserError('Status data sudah Review')
                elif r.state == "complete":
                    raise UserError('Status data sudah Complete')
            res = super(InheritActStockroom, r).action_archive()
        return res

    def button_confirm_complete_multi(self):
        for r in self:
            r.state = 'complete'
            print(r.id, 'confirm to complete')

    def unlink(self):
        for r in self:
            if r.create_uid.id != self.env.user.id:
                raise ValidationError("Data tidak dapat di hapus")
            res = super(InheritActStockroom, r).unlink()
            return res

class InheritActBarging(models.Model):
    _inherit = 'act.barging'

    bu_company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))
    seam_id = fields.Many2one('master.seam', string='Seam Code', required=True)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="Old Bisnis Unit")
    sizing = fields.Selection([
        ('sizing', 'Sizing'),
        ('not sizing', 'Not Sizing'),
    ], default='sizing', string="Sizing")
    basis = fields.Selection([
        ('timbangan', 'Timbangan'),
        ('ritase', 'Ritase'),
    ], default='timbangan', string="Basis")
    active = fields.Boolean(default=True)
    source_group = fields.Many2one('master.sourcegroup', string="Source (Group)", domain=[('name', 'not in', ['BARGE'])])
    item_uom = fields.Many2one("uom.uom", string="Uom", compute="_get_item_uom")
    source_id = fields.Many2one('master.source', string='Source', required=False, help="Tempat pengambilan BatuBara")
    buyer_id = fields.Many2one('res.partner', string='Buyer', required=False, help="Nama Pembeli Batubara")
    kontraktor_produksi_id = fields.Many2one('res.partner', string='Kontraktor Produksi', required=True,
                                    help="kontraktor yang melakukan aktifitas Produksi")
    # buyer_id = fields.Many2one('res.partner', string='Buyer 2', required=True, help="Nama Pembeli Batubara")
    total_unit = fields.Float('Total Fleet', required=True, default=0)

    _sql_constraints = [
        ('positive_volume', 'CHECK(volume >= 0)', 'The Volume must be positive !'),
        ('positive_ritase', 'CHECK(ritase >= 0)', 'The Ritase must be positive !'),
        ('positive_total_unit', 'CHECK(total_unit >= 0)', 'The Total Unit must be positive !')
    ]

    @api.constrains('date_act')
    def _check_date_lock(self):
        if self.state == "draft":
            if cek_date_lock_act("input", self.env.user.id, self.date_act):
                raise UserError(cek_date_lock_act_message("input"))
        print("_check_date_lock")

    # @api.model
    # def create(self, vals):
    #     # for record in self:
    #     if cek_date_lock_act("input", self.env.user.id, vals["date_act"]):
    #         raise UserError(cek_date_lock_act_message("input"))
    #     res = super(InheritActBarging, self).create(vals)
    #     return res

    def action_review(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("review", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("review"))
            res = super(InheritActBarging, record).action_review()
            # raise UserError(cek_date_lock_act_message("review"))
            return res

    def action_approve(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("approve", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("approve"))
            res = super(InheritActBarging, record).action_approve()
            # raise UserError(cek_date_lock_act_message("review"))
            return res

    @api.constrains('kontraktor_id')
    def _check_kontraktor_true(self):
        for record in self:
            if not record.kontraktor_id.is_kontraktor:
                raise ValidationError('kontraktor is true not found')

    @api.constrains('kontraktor_produksi_id')
    def _check_kontraktor_produksi_true(self):
        for record in self:
            if not record.kontraktor_produksi_id.is_kontraktor:
                raise ValidationError('kontraktor Produksi is true not found')

    @api.depends('product')
    def _get_item_uom(self):
        for record in self:
            record.item_uom = record.product.uom_id.id
    @api.constrains('volume')
    def _check_number(self):
        for record in self:
            if record.volume <= 0:
                raise ValidationError('Volume cannot be less than 0')

    @api.onchange('area_id')
    def _onchange_bu_company_id(self):
        self.ensure_one()
        return {
            'domain':
                {
                    'kontraktor_id': [
                        ('company_id', '=', self.bu_company_id.id),
                        ('is_kontraktor', '=', True),
                        ('tipe_kontraktor', '=', 'kontraktor_barging')
                    ],
                    'kontraktor_produksi_id': [
                        ('company_id', '=', self.bu_company_id.id),
                        ('is_kontraktor', '=', True),
                        ('tipe_kontraktor', '=', 'kontraktor_produksi')
                    ],
                    'source_id': [
                        ('bu_company_id', '=', self.bu_company_id.id),
                        ('area_code', '=', self.area_id.id)
                    ]
                }
        }

    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bu_company_id', '=', bu_id)],
                                                                  limit=1)
            vals = []
            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Actual Barging belum disetting')
            result = vals
        return result

    @api.constrains('date_act')
    def _check_date_backdate(self):
        print("Non Active Backdate")

    def action_archive(self):
        for r in self:
            if not r.user_has_groups('bcr_planning_custom_sh.group_bcr_planning_all_archive'):
                if r.state == "review":
                    raise UserError('Status data sudah Review')
                elif r.state == "complete":
                    raise UserError('Status data sudah Complete')
            res = super(InheritActBarging, r).action_archive()
        return res

    def button_confirm_complete_multi(self):
        for r in self:
            r.state = 'complete'
            print(r.id, 'confirm to complete')

    def unlink(self):
        for r in self:
            if r.create_uid.id != self.env.user.id:
                raise ValidationError("Data tidak dapat di hapus")
            res = super(InheritActBarging, r).unlink()
            return res
class InheritActDelay(models.Model):
    _inherit = 'act.delay'

    bu_company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))

    item_uom = fields.Many2one("uom.uom", string="Uom")
    name_uom = fields.Char("name UoM", compute="_get_name_uom", store=True)
    volume_hours = fields.Float('Volume', default=0)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="Old Bisnis Unit")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('positive_volume', 'CHECK(volume >= 0)', 'The Volume must be positive !')
    ]

    @api.constrains('date_act')
    def _check_date_lock(self):
        if self.state == "draft":
            if cek_date_lock_act("input", self.env.user.id, self.date_act):
                raise UserError(cek_date_lock_act_message("input"))
        print("_check_date_lock")

    # @api.model
    # def create(self, vals):
    #     # for record in self:
    #     if cek_date_lock_act("input", self.env.user.id, vals["date_act"]):
    #         raise UserError(cek_date_lock_act_message("input"))
    #     res = super(InheritActDelay, self).create(vals)
    #     return res

    def action_review(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("review", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("review"))
            res = super(InheritActDelay, record).action_review()
            return res

    def action_approve(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("approve", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("approve"))
            res = super(InheritActDelay, record).action_approve()
            return res

    @api.constrains('kontraktor_id')
    def _check_kontraktor_true(self):
        for record in self:
            if not record.kontraktor_id.is_kontraktor:
                raise ValidationError('kontraktor is true not found')

    @api.onchange('area_id')
    def _onchange_bu_company_id(self):
        self.ensure_one()
        return {
            'domain':
                {
                    'kontraktor_id': [
                        ('company_id', '=', self.bu_company_id.id),
                        ('is_kontraktor', '=', True),
                        ('tipe_kontraktor', '=', 'kontraktor_produksi')
                    ]
                }
        }

    @api.onchange('product')
    def onchange_item_uom(self):
        for record in self:
            if record.product:
                record.item_uom = record.product.uom_id
    @api.depends('item_uom')
    def _get_name_uom(self):
        for record in self:
            record.name_uom = record.product.uom_id.name

    @api.onchange('volume_hours')
    def onchange_volume(self):
        for record in self:
            record.volume = record.volume_hours

    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bu_company_id', '=', bu_id)],
                                                                  limit=1)
            vals = []
            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Actual Long Time belum disetting')
            result = vals
        return result

    @api.constrains('date_act')
    def _check_date_backdate(self):
        print("Non Active Backdate")

    def action_archive(self):
        for r in self:
            if not r.user_has_groups('bcr_planning_custom_sh.group_bcr_planning_all_archive'):
                if r.state == "review":
                    raise UserError('Status data sudah Review')
                elif r.state == "complete":
                    raise UserError('Status data sudah Complete')
            res = super(InheritActDelay, r).action_archive()
        return res

    def button_confirm_complete_multi(self):
        for r in self:
            r.state = 'complete'
            print(r.id, 'confirm to complete')

    def unlink(self):
        for r in self:
            if r.create_uid.id != self.env.user.id:
                raise ValidationError("Data tidak dapat di hapus")
            res = super(InheritActDelay, r).unlink()
            return res
class InheritActHauling(models.Model):
    _inherit = 'act.hauling'

    bu_company_id = fields.Many2one('res.company', force_save='1', readonly=True, string='Bisnis Unit', default=lambda self: (self.env.company.id))
    seam_id = fields.Many2one('master.seam', string='Seam Code', required=True)
    bisnis_unit_id = fields.Many2one('master.bisnis.unit', string="Old Bisnis Unit")
    active = fields.Boolean(default=True)
    item_uom = fields.Many2one("uom.uom", string="Uom", compute="_get_item_uom")

    _sql_constraints = [
        ('positive_volume', 'CHECK(volume >= 0)', 'The Volume must be positive !'),
        ('positive_ritase', 'CHECK(ritase >= 0)', 'The Ritase must be positive !'),
        ('positive_total_unit', 'CHECK(total_unit >= 0)', 'The Total Unit must be positive !')
    ]

    @api.constrains('date_act')
    def _check_date_lock(self):
        if self.state == "draft":
            if cek_date_lock_act("input", self.env.user.id, self.date_act):
                raise UserError(cek_date_lock_act_message("input"))
        print("_check_date_lock")

    # @api.model
    # def create(self, vals):
    #     print("print create")
    #     # for record in self:
    #     if cek_date_lock_act("input", self.env.user.id, vals["date_act"]):
    #         raise UserError(cek_date_lock_act_message("input"))
    #     res = super(InheritActHauling, self).create(vals)
    #     return res

    def action_review(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("review", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("review"))
            res = super(InheritActHauling, record).action_review()
            return res

    def action_approve(self):
        for record in self:
            date_act = record.write_date.date()
            # print(date_act, "write_date")
            if cek_date_lock_act("approve", self.env.user.id, date_act):
                raise UserError(cek_date_lock_act_message("approve"))
            res = super(InheritActHauling, record).action_approve()
            return res

    @api.constrains('kontraktor_id')
    def _check_kontraktor_true(self):
        for record in self:
            if not record.kontraktor_id.is_kontraktor:
                raise ValidationError('kontraktor is true not found')

    @api.depends('product')
    def _get_item_uom(self):
        for record in self:
            record.item_uom = record.product.uom_id.id
    @api.onchange('area_id')
    def _onchange_bu_company_id(self):
        self.ensure_one()
        return {
            'domain':
                {
                    'kontraktor_id': [
                        ('company_id', '=', self.bu_company_id.id),
                        ('is_kontraktor', '=', True),
                        ('tipe_kontraktor', '=', 'kontraktor_hauling')
                    ]
                }
        }

    def set_validation(self):
        result = False
        bu_id = self.env.company.id
        if bu_id:
            validation = self.env['validation.validation'].search([('model_id.model', '=', self._name),
                                                                   ('bu_company_id', '=', bu_id)],
                                                                  limit=1)
            vals = []
            if validation:
                for rec in validation.validation_line:
                    vals.append((0, 0, {
                        'user_id': rec.user_id.id,
                        'validation_type_id': rec.validation_type_id.id,
                    }))
            else:
                raise UserError('Validation untuk Form Actual Hauling belum disetting')
            result = vals
        return result

    @api.constrains('date_act')
    def _check_date_backdate(self):
        print("Non Active Backdate")

    def action_archive(self):
        for r in self:
            if not r.user_has_groups('bcr_planning_custom_sh.group_bcr_planning_all_archive'):
                if r.state == "review":
                    raise UserError('Status data sudah Review')
                elif r.state == "complete":
                    raise UserError('Status data sudah Complete')
            res = super(InheritActHauling, r).action_archive()
        return res

    def button_confirm_complete_multi(self):
        for r in self:
            r.state = 'complete'
            print(r.id, 'confirm to complete')

    def unlink(self):
        for r in self:
            if r.create_uid.id != self.env.user.id:
                raise ValidationError("Data tidak dapat di hapus")
            res = super(InheritActHauling, r).unlink()
            return res

# inherit res User

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_default_bisnis_unit_seq_code(self):
        result = False
        user = self.env["res.users"].browse(self._uid)
        if user:
            cek_iup = self.env["master.bisnis.unit"].search([('bu_company_id', '=', self.env.company.id)], limit=1)
            if cek_iup:
                result = cek_iup.seq_code
            else:
                raise UserError('Bisnis Unit harus diinput di Master Bisnis Unit !')

        return result

class SettingBCRparameter(models.Model):
    _name = 'bcr.parameter.setting'
    _description = 'BCR Parameter Setting'

    title = fields.Char(string="Title")
    code = fields.Char(string="Code", readonly=True)
    value = fields.Char(string="Value")
    status = fields.Boolean(string="Status")
    description = fields.Text(string="Description")
    not_allow_user_ids = fields.Many2many('res.users', string="Not Allowed Users")
    # not_allowed_company_ids = fields.Many2many('res.company', string="Not Allowed Company")