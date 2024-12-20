from odoo import models, fields, api, _
# from odoo.exceptions import AccessError, UserError, ValidationError

import logging


_logger = logging.getLogger(__name__)


class FleetEquipment(models.Model):
    _name = "fleet.equipment.class"
    _rec_name = 'code'

    code = fields.Char('Code', store=True, required=True)
    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    _sql_constraints = [
        ('code_company_uniq', 'unique(code)',
         "Code Does Exist"),
    ]


class FleetEquipmentGroup(models.Model):
    _name = "fleet.equipment.group"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    brand_id = fields.Many2one('fleet.brand', string='Brand', store=True, required=True, domain="[('state', '=', 'active')]")
    equipment_class_id = fields.Many2one('fleet.equipment.class', string='Class', store=True, required=True, domain="[('state', '=', 'active')]")
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetBrand(models.Model):
    _name = "fleet.brand"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    _sql_constraints = [
        ('name_company_uniq', 'unique(name)',
         "Brand Does Exist"),
    ]


class InterfaceOps(models.Model):
    _name = "inter.ops"
    _description = "Interface Operational"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    remarks = fields.Text('Remarks')
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetUnit(models.Model):
    _name = "fleet.unit"
    _rec_name = 'name'

    code = fields.Char('Code', store=True, required=True)
    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetActivity(models.Model):
    _name = "fleet.activity"
    _rec_name = 'code'

    code = fields.Char('Code', store=True, required=True)
    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    def name_get(self):
        result = []
        for fleet_act in self:
            operator_name = f"[{fleet_act.code}] {fleet_act.name}"
            result.append((fleet_act.id, operator_name))
        return result


class FleetProcess(models.Model):
    _name = "fleet.process"
    _rec_name = 'code'

    code = fields.Char('Code', store=True, required=True)
    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    def name_get(self):
        result = []
        for fleet_process in self:
            operator_name = f"[{fleet_process.code}] {fleet_process.name}"
            result.append((fleet_process.id, operator_name))
        return result


class FleetMappingAct(models.Model):
    _name = "fleet.map.activity"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetMappingProcess(models.Model):
    _name = "fleet.map.process"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetSubKontraktor(models.Model):
    _name = "fleet.sub.kontraktor"
    _rec_name = 'name'

    kontraktor_id = fields.Many2one('master.fuel.company', string='Kontraktor', store=True, required=True, domain="[('state', '=', 'active')]")
    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetDepartment(models.Model):
    _name = "fleet.department"
    _rec_name = 'name'

    code = fields.Char('Code', store=True, required=True)
    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetCategoryProblem(models.Model):
    _name = "fleet.categ.problem"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    code = fields.Char('Code', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetProblemProdty(models.Model):
    _name = "fleet.problem.prodty"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    code = fields.Char('Code', store=True, required=True)
    categ_id = fields.Many2one('fleet.categ.problem', string='Category', store=True, required=True, domain="[('state', '=', 'active')]")
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetMaterialGroup(models.Model):
    _name = "fleet.material.group"
    _rec_name = 'name'

    name = fields.Char('Name', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetMaterial(models.Model):
    _name = "fleet.material"
    _rec_name = 'name'

    code = fields.Char('Code', store=True, required=True)
    name = fields.Char('Name', store=True, required=True)
    group_id = fields.Many2one('fleet.material.group', string='Group', store=True, required=True, domain="[('state', '=', 'active')]")
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        context = self.env.context
        if context.get('unit_id'):
            unit_equip_id = self.env['fleet.equipment.unit'].browse(context.get('unit_id'))
            domain += [('id', 'in', unit_equip_id.material_ids.ids)]
        else:
            domain += [('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()


class FleetLosttime(models.Model):
    _name = "fleet.losttime"
    _description = "Fleet Losttime"
    _rec_name = 'product_id'

    name = fields.Char('Standby Name', store=True)
    bcr_activity_id = fields.Many2one('master.activity', string='Activity', store=True, required=True, domain="[('code', '=', '01-LT')]")
    sub_activity_id = fields.Many2one('master.sub.activity', string='Sub Activity', store=True, required=True, domain="[('activity_id', '=', bcr_activity_id), ('code', 'in', ('LT-DL', 'LT-ID'))]")
    product_id = fields.Many2one('product.product', string='Standby Name', required=True, domain="[('sub_activity_id', '=', sub_activity_id)]")
    code = fields.Char('Standby Code', related='product_id.default_code')
    uom_id = fields.Many2one('uom.uom', string='Unit Measure', related='product_id.uom_id')
    uom = fields.Char('Unit of Measure', default='Minutes', store=True, readonly=True)
    is_remarks = fields.Boolean('Need Remarks', store=True)
    engine = fields.Boolean('Engine', store=True)
    line_ids = fields.One2many('fleet.losttime.line', 'lost_id', string="Remarks")
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FleetLosttimeLine(models.Model):
    _name = "fleet.losttime.line"
    _rec_name = 'code'

    lost_id = fields.Many2one('fleet.losttime', string='losttime', store=True)
    is_remarks = fields.Boolean('Need Remarks', related='lost_id.is_remarks')
    code = fields.Char('Code', store=True)
    name = fields.Char('Name', store=True)
    department_id = fields.Many2one('fleet.department', string='PIC', store=True, domain="[('state', '=', 'active')]")

    def name_get(self):
        result = []
        for line in self:
            name = f"[{line.code}] {line.name}"
            result.append((line.id, name))
        return result

    @api.model
    def create(self, vals):
        # Create the sale order line first
        res = super(FleetLosttimeLine, self).create(vals)

        # Get the related
        code_losttime = res.lost_id.code
        # Count the number of existing lines
        existing_lines = self.search([('lost_id', '=', res.lost_id.id)])
        line_number = len(existing_lines)

        # Set the custom sequence in format
        res.code = f"{code_losttime}{line_number}"

        return res

    def unlink(self):
        # Get the sale order ID of the lines to be deleted
        lost_id = self.mapped('lost_id.id')

        # Perform the actual delete operation
        res = super(FleetLosttimeLine, self).unlink()

        # After deletion, update the remaining lines' sequence
        remaining_lines = self.search([('lost_id', '=', lost_id)], order="id asc")

        # Reassign the sequence numbers based on remaining lines
        code_losttime = self.env['fleet.losttime'].browse(lost_id).code
        for index, line in enumerate(remaining_lines, start=1):
            line.code = f"{code_losttime}{index}"

        return res
