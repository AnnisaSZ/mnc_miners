from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime, time

from pytz import timezone, UTC

import logging

_logger = logging.getLogger(__name__)


class MnceiEmployee(models.Model):
    _inherit = "mncei.employee"

    def _is_work(self, time_today):
        is_working = False
        calendar_att_obj = self.env['resource.calendar.attendance']
        dayofweek = time_today.strftime("%A")
        if self.shift_temp_ids:
            attendance_id = self.shift_temp_ids.filtered(lambda x: x.start_date <= time_today.date() and x.end_date >= time_today.date())
            if attendance_id:
                resouce_line_id = attendance_id.working_time_id.attendance_ids.filtered(lambda x: dict(calendar_att_obj._fields['dayofweek'].selection).get(x.dayofweek) == dayofweek)
                if resouce_line_id:
                    is_working = True
            else:
                _logger.info("SSSSSSSSSSSSSSSSSSS")
                resouce_line_id = self.working_time_id.attendance_ids.filtered(lambda x: dict(calendar_att_obj._fields['dayofweek'].selection).get(x.dayofweek) == dayofweek)
                _logger.info(resouce_line_id)
                _logger.info(dayofweek)
                if resouce_line_id:
                    _logger.info("SSSSSSSSSSSSSSSSSS00")
                    is_working = True
        else:
            resouce_line_id = self.working_time_id.attendance_ids.filtered(lambda x: dict(calendar_att_obj._fields['dayofweek'].selection).get(x.dayofweek) == dayofweek)
            if resouce_line_id:
                is_working = True
        return is_working
