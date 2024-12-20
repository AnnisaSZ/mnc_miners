from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MasterAircraftType(models.Model):
    _name = 'master.aircraft.type'
    _description = 'Master Aircraft Type'
    _order = 'id desc'
    _rec_name = 'ac_reg'

    name = fields.Char(string='Aircraft Type', required=True)
    ac_reg = fields.Char(string='Registration', required=True)
    qty_max = fields.Integer(string='Seat Capacity', required=True)
    form_ids = fields.One2many('report.fis', 'aircraft_reg_id', string='Form Ids')


class MasterAirport(models.Model):
    _name = 'master.airport'
    _description = 'Master Airport'
    _order = 'name asc'

    name = fields.Char(string='Airport Name', required=True)
    code = fields.Char(string='Airport Code', required=True)
    start_hour = fields.Float('Start Operation Hour', required=True)
    end_hour = fields.Float('End Operation Hour', required=True)
    utc = fields.Integer('UTC', required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)
    city_id = fields.Many2one('res.country.state', string='Province/State', required=True, ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    city = fields.Char(string='City')

    @api.constrains('start_hour', 'end_hour')
    def _check_end_hour(self):
        for form in self:
            if form.start_hour >= 24 or form.end_hour >= 24 or form.start_hour < 0 or form.end_hour < 0:
                raise UserError(_("Invalid time format. Please enter a time between 00:00 and 23:59"))

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, "[%s] - %s" % (rec.code, rec.name)))
        return res
    
    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        domain += ['|', ('code', operator, name), ('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()
    
    def convert_time_to_char(self,time):
        result = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(time) * 60, 60))
        return result

class MasterPosition(models.Model):
    _name = 'master.position'
    _description = 'Master Position'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    crew_ids = fields.One2many('master.crew', 'position_id', string='Crew')

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        domain += ['|', ('code', operator, name), ('name', operator, name)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()


class MasterCrew(models.Model):
    _name = 'master.crew'
    _description = 'Master Crew'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    nik = fields.Char(string='NIK', required=True)
    position_id = fields.Many2one('master.position', string='Position', required=True)
    phone = fields.Char('Phone')

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, "%s - [%s]" % (rec.name, rec.nik)))
        return res

class MasterAgent(models.Model):
    _name = 'master.agent'
    _description = 'Master Agent'
    _order = 'id desc'

    name = fields.Char(string='Agent Name', required=True)
    address = fields.Text(string='Address', size=50)
    phone = fields.Char(string='Phone')
    airport_ids = fields.Many2many('master.airport', string="Airports")
    cp_ids = fields.One2many('master.agent.line', 'parent_id', string='Contact Person', required=True)

    @api.constrains('cp_ids')
    def _check_cp_ids(self):
        for form in self:
            if len(form.cp_ids) == 0:
                raise UserError(_("Please fill in the Contact Person field before saving the data"))

class MasterAgentLine(models.Model):
    _name = 'master.agent.line'
    _description = 'Master Agent Line'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    phone = fields.Char(string='Phone', required=True)
    parent_id = fields.Many2one('master.agent', string='Parent')

class MasterCharterBy(models.Model):
    _name = 'master.charterby'
    _description = 'Master Charter By'
    _order = 'id desc'

    name = fields.Char(string='Company Name', required=True)
    pic = fields.Char(string='PIC')
    phone = fields.Char(string='Contact')
    address = fields.Text(string='Address', size=50)
    form_ids = fields.One2many('report.fis', 'charterby_id', string='Form Ids')

