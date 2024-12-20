from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import math
import logging

_logger = logging.getLogger(__name__)


class MasterShiftMode(models.Model):
    _inherit = 'master.shiftmode'

    shift_line_ids = fields.One2many('master.shiftmode.line', 'shift_mode_id', string='Shift Detail')


class MasterShiftModeLine(models.Model):
    _name = 'master.shiftmode.line'

    shift_mode_id = fields.Many2one('master.shiftmode', string='Shift', ondelete='cascade')
    name = fields.Char('Name', compute='get_compute_name', store=True)
    ttype = fields.Selection([
        ('Day', 'Day'),
        ('Night', 'Night'),
    ], string='Type', required=True)
    start = fields.Float("Start Time", required=True)
    end = fields.Float("End Time", required=True)

    def convert_time(self, time):
        factor = time < 0 and -1 or 1
        val = abs(time)
        # Hours
        hours = factor * int(math.floor(val))
        if hours > 0 and hours < 10:
            hours_char = '0' + str(hours)
        elif hours == 0:
            hours_char = '00'
        else:
            hours_char = str(factor * int(math.floor(val)))
        # Minutes
        minutes = int(round((val % 1) * 60))
        if minutes > 0 and minutes < 10:
            minutes_char = '0' + str(minutes)
        elif minutes == 0:
            minutes_char = '00'
        else:
            minutes_char = str(int(round((val % 1) * 60)))
        # Return Result
        return (hours_char, minutes_char)

    @api.depends('ttype', 'start', 'end')
    def get_compute_name(self):
        for mode_line in self:
            # === Convert ===
            start = ':'.join(mode_line.convert_time(mode_line.start))
            end = ':'.join(mode_line.convert_time(mode_line.end))
            # === /////// ===
            name = _("%s (%s - %s)") % (mode_line.ttype, start, end)
            mode_line.name = name
