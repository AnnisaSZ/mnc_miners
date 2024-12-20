from odoo import api, fields, models, _
from odoo.exceptions import UserError

import firebase_admin
from firebase_admin import credentials, messaging, db
import string
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo.http import request
import requests
import json

from .query_notification import BcrQeuryNotif

import logging
_logger = logging.getLogger(__name__)


def search_usr_validation_by_model(id_parent_model, id_model, state):
    src_user = request.env["validation.plan"].search(
        [(id_parent_model, "=", int(id_model)), ("validation_type_id.code", "=", state)])
    if src_user:
        return src_user


class InheritPlanningHaulingApi(models.Model):
    _inherit = 'planning.hauling'

    def action_start(self):
        res = super(InheritPlanningHaulingApi, self).action_start()
        src_usr_val = search_usr_validation_by_model("validation_planning_hauling_id",self.id, "review")
        if src_usr_val:
            for user in src_usr_val:
                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"planning.hauling", "review",self.kode_planning)
        return res

    @api.constrains('volume_plan')
    def _check_volume(self):
        for plan_hauling in self:
            if plan_hauling.volume_plan <= 0.0:
                raise UserError(_("Volume must be greater than 0"))


class InheritPlanningBargingApi(models.Model):
    _inherit = 'planning.barging'

    def action_start(self):
        res = super(InheritPlanningBargingApi, self).action_start()
        src_usr_val = search_usr_validation_by_model("validation_planning_barging_id",self.id, "review")
        if src_usr_val:
            for user in src_usr_val:
                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"planning.barging", "review",self.kode_planning)
        return res

    @api.constrains('volume_plan')
    def _check_volume(self):
        for plan_barging in self:
            if plan_barging.volume_plan <= 0.0:
                raise UserError(_("Volume must be greater than 0"))


class InheritPlanningProductionApi(models.Model):
    _inherit = 'planning.production'

    def action_start(self):
        res = super(InheritPlanningProductionApi, self).action_start()
        src_usr_val = search_usr_validation_by_model("validation_planning_production_id",self.id, "review")
        if src_usr_val:
            for user in src_usr_val:
                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"planning.production", "review",self.kode_planning)
        return res

    @api.constrains('volume_plan')
    def _check_volume(self):
        for plan_production in self:
            if plan_production.volume_plan <= 0.0:
                raise UserError(_("Volume must be greater than 0"))


class InheritActProductionApi(models.Model):
    _inherit = 'act.production'

    def action_start(self):
        res = super(InheritActProductionApi, self).action_start()
        src_usr_val = search_usr_validation_by_model("validation_act_production_id",self.id, "review")
        if src_usr_val:
            for user in src_usr_val:
                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"act.production", "review",self.kode)
        return res

    @api.constrains('volume')
    def _check_volume(self):
        for act_production in self:
            if act_production.volume <= 0.0:
                raise UserError(_("Volume must be greater than 0"))


class InheritActStockroomApi(models.Model):
    _inherit = 'act.stockroom'

    def action_start(self):
        res = super(InheritActStockroomApi, self).action_start()
        src_usr_val = search_usr_validation_by_model("validation_act_stockroom_id",self.id, "review")
        if src_usr_val:
            for user in src_usr_val:
                request.env['push.notification'].sudo().push_notification_person(user.user_id.login,"act.stockroom", "review",self.kode)
        return res


class InheritActBargingApi(models.Model):
    _inherit = 'act.barging'

    def action_start(self):
        res = super(InheritActBargingApi, self).action_start()
        src_usr_val = search_usr_validation_by_model("validation_act_barging_id", self.id, "review")
        if src_usr_val:
            for user in src_usr_val:
                request.env['push.notification'].sudo().push_notification_person(user.user_id.login, "act.barging",
                                                                                 "review", self.kode)
        return res

    @api.constrains('volume')
    def _check_volume(self):
        for act_barging in self:
            if act_barging.volume <= 0.0:
                raise UserError(_("Volume must be greater than 0"))


class InheritActDelayApi(models.Model):
    _inherit = 'act.delay'

    def action_start(self):
        res = super(InheritActDelayApi, self).action_start()
        src_usr_val = search_usr_validation_by_model("validation_act_delay_id", self.id, "review")
        if src_usr_val:
            for user in src_usr_val:
                request.env['push.notification'].sudo().push_notification_person(user.user_id.login, "act.delay",
                                                                                 "review", self.kode)
        return res

    @api.constrains('volume')
    def _check_volume(self):
        for act_delay in self:
            if act_delay.volume <= 0.0:
                raise UserError(_("Volume must be greater than 0"))


class InheritActHaulingApi(models.Model):
    _inherit = 'act.hauling'

    def action_start(self):
        res = super(InheritActHaulingApi, self).action_start()
        src_usr_val = search_usr_validation_by_model("validation_act_hauling_id", self.id, "review")
        if src_usr_val:
            for user in src_usr_val:
                request.env['push.notification'].sudo().push_notification_person(user.user_id.login, "act.hauling",
                                                                                 "review", self.kode)
        return res

    @api.constrains('volume')
    def _check_volume(self):
        for act_hauling in self:
            if act_hauling.volume <= 0.0:
                raise UserError(_("Volume must be greater than 0"))
