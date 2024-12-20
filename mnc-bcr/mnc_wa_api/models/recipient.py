from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging

TIMEOUT = 20

_logger = logging.getLogger(__name__)


class MinersRecipient(models.Model):
    _name = "miners.recipient"
    _rec_name = "id"

    bod_response_uids = fields.Many2many(
        'res.users', 'bod_response_rel', 'recipient_id', 'responsible_id',
        string='BOD Recipient', store=True, copy=False
    )
    department_recipient_ids = fields.One2many('miners.recipient.department', 'recipient_id', string="Departments")


class MinersRecipientDepartment(models.Model):
    _name = "miners.recipient.department"

    recipient_id = fields.Many2one('miners.recipient', string="Recipient")
    department_id = fields.Many2one('mncei.department', string="Department")
    department_ids = fields.Many2many(
        'mncei.department', 'department_response_rel', 'recipient_id', 'department_id',
        string='Department', store=True, copy=False
    )
    company_ids = fields.Many2many(
        'res.company', 'company_response_rel', 'recipient_id', 'company_id',
        string='Companies', store=True, copy=False
    )
    user_ids = fields.Many2many(
        'res.users', 'user_department_response_rel', 'recipient_id', 'user_department_id',
        string='Recipient', store=True, copy=False
    )
