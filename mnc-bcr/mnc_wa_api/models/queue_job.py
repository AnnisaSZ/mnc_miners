from odoo import _, api, exceptions, fields, models
import logging
import json

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    """Model storing the jobs to be executed."""
    _inherit = "queue.job"

    def _to_send_whatsapp(self, datas, user_id):
        qontak_auth_obj = self.env['qontak.auth']
        uri = datas['uri']
        data = datas['data']
        headers = datas['headers']
        status, response = qontak_auth_obj._do_request(uri, json.dumps(data), headers, 'POST')
        qontak_auth_obj.create_logging(user_id, status, response)

    def _to_send_report(self, datas):
        _logger.info("Running test job.")
        attendance_obj = self.env['hr.attendance']
        employee_id = datas['employee_id']
        last_7_days = list(reversed(datas['last_7_days']))
        attendance_obj.send_resume_weekly(employee_id, last_7_days)
