from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class MasterActivity(models.Model):
    _name = 'view.inventory'
    _description = 'Sql View Table Inventory'
    _auto = False

    sub_activity = fields.Char("Sub Activity")
    bisnis_unit = fields.Char("Bisnis Unit")
    pit = fields.Char("Pit")
    seam = fields.Char("Seam")
    date = fields.Date("Date")
    volume = fields.Float("Volume")
    bu_id = fields.Char("Bisnis Unit ID")

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW view_inventory
             AS
             (SELECT sa.name AS sub_activity,
                cp.name AS bisnis_unit,
                ar.name AS pit,
                se.code AS seam,
                inv.date_act AS date,
                inv.volume,
                cp.id AS bu_id
               FROM act_stockroom inv
                 LEFT JOIN master_sub_activity sa ON inv.activity_id = sa.activity_id AND sa.active = true AND inv.sub_activity_id = sa.id
                 LEFT JOIN res_company cp ON cp.active = true AND inv.bu_company_id = cp.id
                 LEFT JOIN master_area ar ON ar.active = true AND inv.area_id = ar.id
                 LEFT JOIN master_seam se ON inv.bu_company_id = se.bu_company_id AND inv.seam_id = se.id
              WHERE inv.active = true AND inv.state = 'complete'
              )
        """)
