import json
import pytz
import base64
import calendar
import datetime

from odoo import http, SUPERUSER_ID, _
from pytz import UTC
from datetime import datetime, timedelta
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import fields


class BcrQueryHazard(Exception):

    # Pelapor
    def QueryTableReport(self, user_id, date_start, date_end):
        query = '''
            select status,
            count(case when kategori = 'KTA' then kategori end) KTA,
            count(case when kategori = 'TTA' then kategori end) TTA,
            count(case when kategori = 'KA' then kategori end) KA,
            count(case when kategori = 'TA' then kategori end) TA

            from
                (
                    select
                    us.login Report_User,
                    us2.login Fixing_User,
                    sap.state status,
                    ch.code Kategori,
                    sap.create_uid, sap.act_repair_uid,
                    sap.incident_date_time
                    from sapform sap
                    left join res_users us on sap.create_uid = us.id
                    left join res_users us2 on sap.act_repair_uid=us2.id
                    left join category_hazard ch on sap.categ_id=ch.id
                    where sap.active=true
                )data

            where data.create_uid=%s
                    and data.incident_date_time >= '%s'
                    and data.incident_date_time  <=  '%s'
            and status<>'draft'
            group by status
        ''' % (user_id, date_start, date_end)
        # date = '10/01/2023 00:00:00'
        return query

    # Fixing
    def QueryTableFixing(self, user_id, date_start, date_end):
        query = '''
            select status,
            count(case when kategori = 'KTA' then kategori end) KTA,
            count(case when kategori = 'TTA' then kategori end) TTA,
            count(case when kategori = 'KA' then kategori end) KA,
            count(case when kategori = 'TA' then kategori end) TA

            from
                (
                    select
                    us.login Report_User,
                    us2.login Fixing_User,
                    sap.state status,
                    ch.code Kategori,
                    sap.create_uid, sap.act_repair_uid,
                    sap.incident_date_time
                    from sapform sap
                    left join res_users us on sap.create_uid = us.id
                    left join res_users us2 on sap.act_repair_uid=us2.id
                    left join category_hazard ch on sap.categ_id=ch.id
                    where sap.active=true
                )data

            where data.act_repair_uid=%s
            and data.incident_date_time >= '%s'
            and data.incident_date_time  <=  '%s'
            and status<>'draft'
            group by status
        ''' % (user_id, date_start, date_end)
        # date = '10/01/2023 00:00:00'
        return query
