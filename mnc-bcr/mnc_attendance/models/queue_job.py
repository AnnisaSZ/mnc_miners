from odoo import _, api, exceptions, fields, models
import logging

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    """Model storing the jobs to be executed."""
    _inherit = "queue.job"

    def _create_attendance(self, datas):
        _logger.info("Running test job.")
        attendance_obj = self.env['hr.attendance']
        start_date = datas['start_date']
        end_date = datas['end_date']
        employee_code = datas['employee_code']
        is_shift = datas['is_shift']
        attendance_obj.action_get_transaction(start_date, end_date, employee_code, is_shift)

    def get_token_wdms(self, res_id):
        wdms_user_id = self.env['wdms.config'].browse(res_id)
        wdms_user_id.action_get_token()
