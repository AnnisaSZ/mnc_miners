from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta


class ReportFis(models.Model):
    _name = 'report.fis'
    _description = 'Report FIS'
    _order = 'id desc'

    name = fields.Char(string='Flight No.', required=True)

    def default_request_date(self):
        res = (datetime.today() + timedelta(hours=int(8)))
        return res
    
    request_date = fields.Date(string='Date', required=True, default=default_request_date)
    aircraft_reg_id = fields.Many2one('master.aircraft.type', string='Registration', required=True)
    aircraft_type = fields.Char(string='Aircraft Type', related='aircraft_reg_id.name')
    aircraft_qty = fields.Integer(string='Seat Capacity', related='aircraft_reg_id.qty_max')
    charterby_id = fields.Many2one('master.charterby', string='Chartered By', required=True)

    airport_ids = fields.Many2many('master.airport', string='Airport ids')
    
    # Flight Schedule
    flight_schedule_ids = fields.One2many('flight.schedule.line', 'form_id')
    last_airport_id = fields.Many2one('master.airport')
    last_date = fields.Date("last date")
    sum_flight_time = fields.Char('Duration Flight', compute="_compute_flight_time", store=True)
    notes = fields.Text('Airport Information', compute="_compute_flight_time", store=True)

    # Crew Detail
    crew_detail_ids = fields.One2many('crew.detail.line', 'form_id')
    used_crew_ids = fields.Many2many('master.crew', string="Crew Member")

    # Handling Agent
    handling_agent_ids = fields.One2many('handling.agent.line', 'form_id')

    # Passenger
    passenger_ids = fields.One2many('passenger.line', 'form_id')

    # Crew Accomodation
    crew_ids = fields.One2many('crew.accomodation.line', 'form_id')

    # Other Information
    status_clearance = fields.Char(string="Flight Sec. Clearance", store=True)
    status_approval = fields.Char(string="Flight Approval", store=True)
    status_fuel = fields.Char(string="Fuel On Board", store=True)
    status_notam = fields.Char(string="Notam", store=True)
    status_parking = fields.Char(string="Parking Stand", store=True)

    # version
    print_count = fields.Integer(string="Print Count", default=1)

    # @api.onchange('charterby_id')
    # def _onchange_charterby_id(self):

    # @api.constrains('handling_agent_ids')
    # def _check_handling_agent_ids(self):
    #     for form in self:
    #         check_handling_agent_ids = self.handling_agent_ids.filtered(lambda x: not x.agent_id)
    #         if check_handling_agent_ids:
    #             raise UserError(_("Please fill in the Company field at Handling Agents before saving the data"))

    @api.onchange('flight_schedule_ids', 'flight_schedule_ids.start_airport', 'flight_schedule_ids.end_airport')
    def _onchange_handling_agent_ids(self):
        airport_ids = list(set(self.flight_schedule_ids.mapped('start_airport').ids + self.flight_schedule_ids.mapped('end_airport').ids))
        if self.flight_schedule_ids:
            self.last_airport_id = self.flight_schedule_ids[-1].end_airport
        self.airport_ids = airport_ids
        
        # Handling Agent
        unused_handling_agent = self.handling_agent_ids.filtered(lambda x: x.location_id.id not in airport_ids)
        unused_handling_agent.write({'form_id':False})
        # Crew Accomodation
        unused_crew_ids = self.crew_ids.filtered(lambda x: x.location_id.id not in airport_ids)
        unused_crew_ids.write({'form_id':False})


        get_aiport = (set(airport_ids)-(set(self.handling_agent_ids.mapped('location_id').ids)))
        for airport in get_aiport:
            self.env['handling.agent.line'].create({'location_id':airport, 'form_id':self.id})
            self.env['crew.accomodation.line'].create({'location_id':airport, 'form_id':self.id})

    @api.onchange('request_date', 'flight_schedule_ids', 'flight_schedule_ids.date')
    def _onchange_last_date(self):
        flight_date = max(list(set(self.flight_schedule_ids.mapped('date') + [self.request_date])))
        self.last_date = flight_date

    def write(self, vals):
        for rec in self:
            if 'print_count' not in vals:
                rec.print_count += 1
        return super(ReportFis, self).write(vals)

    @api.depends('flight_schedule_ids')
    def _compute_flight_time(self):
        for rec in self:
            info = ""
            airport = False
            sum_flight_time = sum(line.total_flight for line in rec.flight_schedule_ids)
            rec.sum_flight_time = '{0:02.0f} Jam {1:02.0f} Menit'.format(*divmod(float(sum_flight_time) * 60, 60))

            list_airport = list(set(rec.flight_schedule_ids.mapped('start_airport')+rec.flight_schedule_ids.mapped('end_airport')))
            for airport in list_airport:
                if airport.city:
                    info += airport.city + " (" + airport.code + ") - " + airport.name + " - " + airport.convert_time_to_char(airport.start_hour) + " - " + airport.convert_time_to_char(airport.end_hour) + "\n"
            rec.notes = info

    @api.onchange('crew_detail_ids','crew_detail_ids.crew_id')
    def _onchange_crew_detail_ids(self):
        self.used_crew_ids = self.crew_detail_ids.mapped('crew_id')
        return
    
                    
class FlightScheduleLine (models.Model):
    _name = 'flight.schedule.line'
    _description = 'Flight Schedule Line'
    _rec_name = 'start_airport'

    name = fields.Char(string='Flight No.')
    date = fields.Date(string='Date', required=True)
    date_domain = fields.Date(string='Date')
    start_airport = fields.Many2one('master.airport', string='From', required=True)
    end_airport = fields.Many2one('master.airport', string='To', required=True)
    eta = fields.Float('ETA')
    etd = fields.Float('ETD')
    total_flight = fields.Float('Total Flight', compute='calc_flight_time', store=True)
    remarks = fields.Char('Remarks')

    form_id = fields.Many2one('report.fis', string='Form ID')

    @api.onchange('start_airport', 'end_airport')
    def _onchange_airport(self):
        for rec in self:
            if rec.start_airport or rec.end_airport:
                company_airport_start = company_airport_end = True
                airport = False
                if rec.start_airport:
                    company_airport_start = self.env['master.agent'].search([('airport_ids', 'in', rec.start_airport.ids)])
                    airport = rec.start_airport.name
                if rec.end_airport:
                    company_airport_end = self.env['master.agent'].search([('airport_ids', 'in', rec.end_airport.ids)])
                    airport = rec.end_airport.name
                # if not company_airport_start or not company_airport_end:
                #     raise ValidationError(_('The agent for the selected location (' + airport + ') has not been configured in the master data. Please ensure the agent is set before proceeding.'))
    
    @api.onchange('date')
    def onchange_date(self):
        if self.date:
            if self.date_domain:
                if self.date < self.date_domain:
                    self.date = False
                    raise ValidationError(_("The selected date cannot be earlier than the previously chosen date. Please select a later date."))
            else:
                self.date = False
                raise ValidationError(_("The Date field must be completed before entering the Date in the Flight Schedule section. Please fill in the required date."))
        return 
    
    @api.constrains('eta', 'etd')
    def _check_end_hour(self):
        for form in self:
            if form.eta >= 24 or form.etd >= 24 or form.eta < 0 or form.etd < 0:
                raise UserError(_("Invalid time format. Please enter a time between 00:00 and 23:59"))

    @api.depends('eta', 'etd')
    def calc_flight_time(self):
        for rec in self:
            dif_utc = rec.end_airport.utc - rec.start_airport.utc
            total_flight = (((rec.eta+24)-rec.etd) - dif_utc) if (rec.eta<rec.etd) else rec.eta-rec.etd-dif_utc
            hour, minute = divmod(total_flight, 1)
            minute *= 60

            rec.total_flight = total_flight

class CrewDetailLine (models.Model):
    _name = 'crew.detail.line'
    _description = 'Crew Detail Line'
    _rec_name = 'crew_id'

    name = fields.Char(string='Name')
    crew_id = fields.Many2one('master.crew', string='Name', required=True)
    position_id = fields.Many2one('master.position', string='Position', related="crew_id.position_id")
    phone = fields.Char(string='Phone', related="crew_id.phone")
    remarks = fields.Char('Remarks')

    form_id = fields.Many2one('report.fis', string='Form ID')


class HandlingAgentLine (models.Model):
    _name = 'handling.agent.line'
    _description = 'Handling Agent Line'
    _rec_name = 'location_id'

    location_id = fields.Many2one('master.airport', string='Location', required=True)
    agent_id = fields.Many2one('master.agent', string='Company')
    cp_id = fields.Many2one('master.agent.line', string='Contact Person')
    phone = fields.Char(string='Phone', related="cp_id.phone")

    form_id = fields.Many2one('report.fis', string='Form ID')
    
    @api.onchange('agent_id')
    def _onchange_agent_id(self):
        for rec in self:
            cp_id = False
            if len(rec.agent_id.cp_ids) == 1:
                cp_id = rec.agent_id.cp_ids.id
            rec.cp_id = cp_id

class PassengerLine (models.Model):
    _name = 'passenger.line'
    _description = 'Passenger Line'

    name = fields.Char(string='Name', required=True)
    remarks = fields.Char('Remarks')

    form_id = fields.Many2one('report.fis', string='Form ID')

class CrewAccomodationLine (models.Model):
    _name = 'crew.accomodation.line'
    _description = 'Crew Accomodation Line'
    _rec_name = 'location_id'

    location_id = fields.Many2one('master.airport', string='Location', required=True)
    name = fields.Char(string='Hotel')
    address = fields.Char(string='Address')
    phone = fields.Char(string='Phone')

    form_id = fields.Many2one('report.fis', string='Form ID')

    