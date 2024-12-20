from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


# Master Unit
class MasterUnit(models.Model):
    _name = "master.fuel.unit"
    _description = "Master Unit"
    _rec_name = "kode_unit"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    company_id = fields.Many2one(
        'res.company',
        string='IUP', store=True, default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    kode_unit = fields.Char(string='Kode Unit', size=55, store=True, required=True)
    jenis_unit_id = fields.Many2one('master.jenis.unit', string='Jenis Unit', store=True, required=True, domain="[('state', '=', 'active')]")
    tipe_unit_id = fields.Many2one('master.fuel.type.unit', string='Tipe Unit', store=True, required=True, domain="[('company_id', '=', company_id), ('state', '=', 'active'), ('jenis_unit_id', '=', jenis_unit_id)]")
    merk_unit_id = fields.Many2one('master.merk.unit', string='Merk Unit', store=True, required=True, domain="[('state', '=', 'active')]")
    tahun = fields.Char(string='Tahun', size=6, store=True, required=True)
    tank_capacity = fields.Char(string='Tank Capacity', size=21, store=True, required=True)
    company_fuel_id = fields.Many2one('master.fuel.company', string='Kontraktor', size=75, store=True, required=True, domain="[('state', '=', 'active'), ('company_ids', 'in', company_id)]")
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)
    fuel_truck = fields.Boolean('Fuel Truck', store=True)
    standard_high = fields.Float('High', store=True)
    standard_low = fields.Float('Low', store=True)
    is_hm = fields.Boolean('HM', store=True)
    is_km = fields.Boolean('KM', store=True)

    @api.constrains('kode_unit')
    def _check_code_unit(self):
        for unit in self:
            unit_ids = self.env['master.fuel.unit'].search([('kode_unit', '=', unit.kode_unit), ('company_id', '=', unit.company_id.id), ('id', '!=', unit.id)])
            if unit_ids:
                raise ValidationError(_("Code Unit must be unique"))

    # @api.constrains('jenis_unit_id')
    # def _check_jenis_unit(self):
    #     for unit in self:
    #         unit_ids = self.env['master.fuel.unit'].search([('jenis_unit_id', '=', unit.jenis_unit_id.id), ('id', '!=', unit.id)])
    #         if unit_ids:
    #             raise ValidationError(_("Jenis Unit must be unique"))

    @api.onchange('jenis_unit_id')
    def change_type_unit(self):
        if self.jenis_unit_id:
            self.tipe_unit_id = False


class MasterJenisUnit(models.Model):
    _name = "master.jenis.unit"
    _description = "Jenis Unit"

    name = fields.Char('Jenis Unit', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    _sql_constraints = [
        ('unique_code', 'unique(name)',
         'This name is already exits.'),
    ]

    @api.constrains('name')
    def _check_code_unit(self):
        for jenis_unit in self:
            jenis_unit_ids = self.env['master.jenis.unit'].search([('name', '=', jenis_unit.name), ('id', '!=', jenis_unit.id)])
            if jenis_unit_ids:
                raise ValidationError(_("Name must be unique"))


class MasterMerkUnit(models.Model):
    _name = "master.merk.unit"
    _description = "Merk Unit"

    name = fields.Char('Nama Merk', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    _sql_constraints = [
        ('unique_code', 'unique(name)',
         'This name is already exits.'),
    ]

    @api.constrains('name')
    def _check_code_unit(self):
        for merk_unit in self:
            merk_unit_ids = self.env['master.merk.unit'].search([('name', '=', merk_unit.name), ('id', '!=', merk_unit.id)])
            if merk_unit_ids:
                raise ValidationError(_("Name must be unique"))


# Master Type Unit
class MasterTypeUnit(models.Model):
    _name = "master.fuel.type.unit"
    _description = "Master Type Unit"
    _rec_name = "tipe_unit"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    company_id = fields.Many2one(
        'res.company',
        string='IUP', store=True, default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    tipe_unit = fields.Char(string='Tipe Unit', size=75, store=True, required=True)
    jenis_unit_id = fields.Many2one('master.jenis.unit', string='Jenis Unit', store=True, required=True, domain="[('state', '=', 'active')]")
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    # _sql_constraints = [
    #     ('unique_code', 'unique(tipe_unit)',
    #      'This name type unit is already exits.'),
    # ]

    @api.constrains('name')
    def _check_code_unit(self):
        for fuel_type in self:
            fuel_type_ids = self.env['master.fuel.type.unit'].search([('tipe_unit', '=', fuel_type.tipe_unit), ('company_id', '=', fuel_type.company_id.id), ('id', '!=', fuel_type.id)])
            if fuel_type_ids:
                raise ValidationError(_("Name must be unique"))


# Master Perusahaan
class MasterContractor(models.Model):
    _name = "master.fuel.company"
    _description = "Master Kontraktor"
    _rec_name = "name_company_fuel"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    name_company_fuel = fields.Char(string='Contractor Company', size=75, store=True, required=True)
    company_ids = fields.Many2many('res.company', string="IUP", domain=_company_ids_domain, store=True)
    code_comp_fuel = fields.Char(string='Kode Kontraktor', size=55, store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


# Master Driver
class MasterDriver(models.Model):
    _name = "master.fuel.driver"
    _description = "Master Driver"

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    company_id = fields.Many2one(
        'res.company',
        string='IUP', store=True, default=lambda self: self.env.company, domain=_company_ids_domain, required=True
    )
    kode_driver = fields.Char(string='Kode Driver', size=55, store=True, required=True)
    nama_driver = fields.Char(string='Nama Driver', size=55, store=True, required=True)
    company_fuel_id = fields.Many2one('master.fuel.company', size=75, store=True, required=True, domain="[('state', '=', 'active'), ('company_ids', 'in', company_id)]")
    phone = fields.Char(string='Phone', size=55, store=True)
    # unit_id = fields.Many2one('master.fuel.unit', store=True, required=True, domain="[('state', '=', 'active')]")
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    def name_get(self):
        result = []
        for driver in self:
            combine_name = _("[%s] %s") % (driver.kode_driver, driver.nama_driver)
            name = combine_name
            result.append((driver.id, name))
        return result

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        domain += ['|', ('kode_driver', operator, name), ('nama_driver', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()


# Master Fuelman
class MasterFuelman(models.Model):
    _name = "master.fuel.fuelman"
    _description = "Master Fuelman"
    _rec_name = "nama_fuelman"

    kode_fuelman = fields.Char(string='Kode Fuelman', size=55, store=True, required=True)
    nama_fuelman = fields.Char(string='Nama Fuelman', size=55, store=True, required=True)
    company_fuel_id = fields.Many2one('master.fuel.company', size=75, store=True, required=True)
    phone = fields.Char(string='Phone', size=55, store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


# Master Foreman
class MasterForeman(models.Model):
    _name = "master.fuel.foreman"
    _description = "Master Foreman"
    _rec_name = "nama_foreman"

    kode_foreman = fields.Char(string='Fuelman', size=55, store=True, required=True)
    nama_foreman = fields.Char(string='Nama Foreman', size=55, store=True, required=True)
    company_fuel_id = fields.Many2one('master.fuel.company', size=75, store=True, required=True)
    phone = fields.Char(string='Phone', size=55, store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class MasterFuelUser(models.Model):
    _name = "master.fuel.user"
    _description = "Master User Fuel"

    name = fields.Char(string='Nama', size=55, store=True, required=True)
    company_fuel_id = fields.Many2one('master.fuel.company', size=75, store=True, required=True)
    phone = fields.Char(string='Phone', size=55, store=True, required=True)
    ttype = fields.Selection([
        ('engineering', 'Engineering Operation'),
        ('pjo', 'PJO'),
    ], default='engineering', string="Type User", required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)


class FuelLokasiKerja(models.Model):
    _name = "fuel.lokasi.kerja"
    _description = "Lokasi Kerja"

    name = fields.Char('Lokasi Kerja', store=True, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], default='active', store=True, required=True)

    # _sql_constraints = [
    #     ('unique_code', 'unique(name)',
    #      'This name location working is already exits.'),
    # ]
