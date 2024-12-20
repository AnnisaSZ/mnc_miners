from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging


_logger = logging.getLogger(__name__)


class FleetMasterLocationGroup(models.Model):
    _name = "fleet.master.location.group"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetMasterLocation(models.Model):
    _name = "fleet.master.location"
    _description = "Fleet Location"
    _rec_name = 'name'

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    # From Master Unit - Fuel
    company_id = fields.Many2one('res.company', string='IUP', store=True, required=True, domain=_company_ids_domain)
    name = fields.Char('Name', store=True, required=True)
    group_id = fields.Many2one('fleet.master.location.group', string='Group', store=True, required=True, domain="[('state', '=', 'active')]")
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetMasterOperator(models.Model):
    _name = "fleet.master.operator"
    _description = "Fleet operator"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    # From Master Unit - Fuel
    company_id = fields.Many2one('res.company', string='IUP', store=True, required=True, domain=_company_ids_domain)
    name = fields.Char('Name', store=True, required=True)
    nik = fields.Char('NIK', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    def name_get(self):
        result = []
        for operator in self:
            nik = operator.nik
            name = operator.name
            operator_name = f"[{nik}] {name}"
            result.append((operator.id, operator_name))
        return result


class FleetMasterEqpAct(models.Model):
    _name = "fleet.equipment.activity"
    _rec_name = 'activity_name'

    class_id = fields.Many2one('fleet.equipment.class', string='Equipment Class', store=True, required=True, domain="[('state', '=', 'active')]")
    fleet_activity_id = fields.Many2one('fleet.activity', string='Activity Code', store=True, required=True, domain="[('state', '=', 'active')]")
    activity_name = fields.Char('Activity Name', related='fleet_activity_id.name', store=True)
    process_id = fields.Many2one('fleet.process', string='Process Code', store=True, required=True, domain="[('state', '=', 'active')]")
    process_name = fields.Char('Process Name', related='process_id.name', store=True)
    material_id = fields.Many2one('fleet.material', string='Material Code', store=True, required=True, domain="[('state', '=', 'active')]")
    material_group_id = fields.Many2one('fleet.material.group', string='Material Group', related='material_id.group_id')
    # material_groups = fields.Selection([
    #     ('coal', 'Coal'),
    #     ('ob', 'OB'),
    # ], related='material_id.groups', store=True, required=True)
    location_id = fields.Many2one('fleet.master.location.group', string='Source Group', store=True, required=True, domain="[('state', '=', 'active')]")
    destination_id = fields.Many2one('fleet.master.location.group', string='Destination Group', store=True, required=True, domain="[('state', '=', 'active')]")
    # location_name = fields.Char('Destination Group', related='location_id.name', store=True)
    map_act_id = fields.Many2one('fleet.map.activity', string='Mapping Activity', store=True, required=True, domain="[('state', '=', 'active')]")
    map_process_id = fields.Many2one('fleet.map.process', string='Mapping Process', store=True, required=True, domain="[('state', '=', 'active')]")


class FleetEquipmentUnits(models.Model):
    _name = "fleet.equipment.unit"
    _rec_name = 'number'

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    # From Master Unit - Fuel
    company_id = fields.Many2one('res.company', string='IUP', store=True, required=True, domain=_company_ids_domain)
    kontraktor_id = fields.Many2one('master.fuel.company', string='Kontraktor', store=True, required=True, domain="[('state', '=', 'active'), ('company_ids', 'in', company_id)]")
    fuel_unit_id = fields.Many2one('master.fuel.unit', string='Unit', store=True, required=True, domain="[('company_id', '=', company_id), ('company_fuel_id', '=', kontraktor_id)]")
    # ====================================
    number = fields.Char('Number', store=True, related='fuel_unit_id.kode_unit')
    years = fields.Char('Years', related='fuel_unit_id.tahun')
    equipment_group_id = fields.Many2one('fleet.equipment.group', string='Equipment Groups', store=True, required=True, domain="[('state', '=', 'active')]")
    equipment_class_id = fields.Many2one('fleet.equipment.class', string='Class Name', related='equipment_group_id.equipment_class_id', store=True)
    equip_class_code = fields.Char('Class Code', related='equipment_class_id.code', store=True)
    brand_id = fields.Many2one('fleet.brand', string='Brand', related='equipment_group_id.brand_id', store=True)
    shift_mode_id = fields.Many2one('master.shiftmode', string='Shift Mode', store=True, required=True)
    sub_kontraktor_id = fields.Many2one('fleet.sub.kontraktor', string='Keterangan', domain="[('kontraktor_id', '=', kontraktor_id)]", store=True, required=True)
    interface_id = fields.Many2one('inter.ops', string='Interface', store=True, required=True)
    state_unit_id = fields.Many2one('fleet.unit', string='Status Unit', store=True, required=True)
    is_timesheet = fields.Boolean('Timesheets', store=True)
    is_loader = fields.Boolean('Loader', store=True)
    fc_standard = fields.Float('FC Standard(L/hr)', store=True)
    # Lines
    material_ids = fields.Many2many('fleet.material', string='Material', compute='_compute_material', store=True)
    line_ids = fields.One2many('equipment.unit.line', 'equip_unit_id', compute='_compute_material', string="Material", store=True)

    @api.onchange('company_id', 'kontraktor_id')
    def onchange_unit(self):
        if self.fuel_unit_id:
            self.fuel_unit_id = False

    @api.depends('equipment_group_id', 'interface_id')
    def _compute_material(self):
        for unit in self:
            unit.line_ids = False
            unit.material_ids = False
            res_data = []
            materials = []
            if unit.equipment_group_id:
                if unit.equipment_group_id.line_ids:
                    for line in unit.equipment_group_id.line_ids:
                        # Line data
                        res_data.append((0, 0, {
                            'equip_unit_id': line.equip_unit_id.id,
                            'fleet_material_id': line.fleet_material_id.id,
                            'capacity_unit': line.capacity_unit,
                            'plan_product': line.plan_product,
                        }))
                        # Material
                        materials.append(line.fleet_material_id.id)
            unit.line_ids = res_data
            unit.material_ids = [(6, 0, materials)]


class FleetEquipmentGroup(models.Model):
    _inherit = "fleet.equipment.group"

    # Material
    line_ids = fields.One2many('equipment.unit.line', 'equip_group_id', string="Material")
    unit_equip_ids = fields.One2many('fleet.equipment.unit', 'equipment_group_id', string="Unit Equipment")

    def write(self, vals):
        res = super(FleetEquipmentGroup, self).write(vals)
        if vals.get('line_ids'):
            for unit in self.unit_equip_ids:
                unit._compute_material()
        return res


class EquipUnitsLine(models.Model):
    _name = "equipment.unit.line"
    _rec_name = 'equip_unit_id'

    equip_unit_id = fields.Many2one('fleet.equipment.unit', string='Equipment Unit', store=True)
    equip_group_id = fields.Many2one('fleet.equipment.group', string='Equipment Group', store=True)
    fleet_material_id = fields.Many2one('fleet.material', string='Material', store=True)
    capacity_unit = fields.Float('Capacity Units', store=True)
    plan_product = fields.Float('Plan Productivity', store=True)


class MasterShiftModeLine(models.Model):
    _inherit = 'master.shiftmode.line'

    timerange_ids = fields.One2many('fleet.timerange', 'shift_line_id', string='Time Range')

    def add_timerange(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({
            'create': False,
        })
        view_id = self.env.ref('mnc_fleet.fleet_time_range').id
        return {
            'name': _("Input Timerange"),
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'master.shiftmode.line',
            'view_id': view_id,
            'context': context
        }


class MasterTimeRange(models.Model):
    _name = 'fleet.timerange'
    _description = "Time Range"

    shift_line_id = fields.Many2one('master.shiftmode.line', string='Shift Line', ondelete='cascade')
    name = fields.Char('Name', compute='_compute_name')
    time_from = fields.Integer('From', store=True, required=True)
    time_to = fields.Integer('To', store=True, required=True)

    @api.depends('time_from', 'time_to')
    def _compute_name(self):
        for timerange in self:
            name = _("%d To %d") % (timerange.time_from, timerange.time_to)
            timerange.name = name


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains('uom_id', 'uom_po_id')
    def _check_uom(self):
        context = self.env.context
        if any(template.uom_id and template.uom_po_id and template.uom_id.category_id != template.uom_po_id.category_id for template in self) and not context.get('fleet'):
            raise ValidationError(_('The default Unit of Measure and the purchase Unit of Measure must be in the same category.'))
        return True
