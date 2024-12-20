import logging
import werkzeug.wrappers
from datetime import datetime, date
import pytz
import dateutil.parser
from odoo import http, SUPERUSER_ID
from odoo.http import request
import requests
from odoo.tools.safe_eval import safe_eval
import json
import base64

from pytz import utc
from odoo import api, fields, models, tools

class BcrQeuryNotif(Exception):

    def QueryNotifDaily(self):
        query = "DO $$ "\
                "DECLARE startdate date; stopdate date; activity text; "\
                "BEGIN "\
                "    SELECT current_date - INTEGER '1' INTO startdate; "\
                "	SELECT current_date - INTEGER '1' INTO stopdate; "\
                "    DROP TABLE IF EXISTS prod_akt; "\
                "	DROP TABLE IF EXISTS prod_plan; "\
                "    DROP TABLE IF EXISTS hauling_akt; "\
                "	DROP TABLE IF EXISTS hauling_plan; "\
                "	DROP TABLE IF EXISTS barging_akt; "\
                "	DROP TABLE IF EXISTS barging_plan; "\
                "	DROP TABLE IF EXISTS resume; "\
                "    CREATE TABLE prod_akt AS "\
                "    select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	sa.name Sub_Activity, "\
                "	sum(ap.volume) volume "\
                "	 from act_production ap "\
                "	left join master_sub_activity sa on sa.id = ap.sub_activity_id "\
                "	left join res_company cp on ap.bu_company_id = cp.id "\
                "	where  ap.date_act between startdate and stopdate "\
                "	and ap.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "    CREATE TABLE prod_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' Sub_Activity, "\
                "	sa.name, "\
                "	sum(pp.volume_plan) volume "\
                "	 from planning_production pp "\
                "	left join master_sub_activity sa on sa.id = pp.sub_activity_id "\
                "	left join res_company cp on pp.bu_company_id = cp.id "\
                "	where pp.date_START between startdate and stopdate "\
                "	and pp.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE hauling_akt AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' else sa.name end Sub_Activity, "\
                "	sum(ah.volume) volume "\
                "	 from act_hauling ah "\
                "	left join master_sub_activity sa on sa.id = ah.sub_activity_id "\
                "	left join res_company cp on ah.bu_company_id = cp.id "\
                "	where  ah.date_act between startdate and stopdate "\
                "	and ah.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE hauling_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' item, "\
                "	case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' else sa.name end  Sub_Activity, "\
                "	sum(ph.volume_plan) volume "\
                "	 from planning_hauling ph "\
                "	left join master_sub_activity sa on sa.id = ph.sub_activity_id "\
                "	left join res_company cp on ph.bu_company_id = cp.id "\
                "	where ph.date_START between startdate and stopdate "\
                "	and ph.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE barging_akt AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	sa.name Sub_Activity, "\
                "	sum(ab.volume) volume "\
                "	 from act_barging ab "\
                "	left join master_sub_activity sa on sa.id = ab.sub_activity_id "\
                "	left join res_company cp on ab.bu_company_id = cp.id "\
                "	where  ab.date_act between startdate and stopdate "\
                "	and ab.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE barging_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' item, "\
                "	sa.name Sub_Activity, "\
                "	sum(pb.volume_plan) volume "\
                "	 from planning_barging pb "\
                "	left join master_sub_activity sa on sa.id = pb.sub_activity_id "\
                "	left join res_company cp on pb.bu_company_id = cp.id "\
                "	where pb.date_START between startdate and stopdate "\
                "	and pb.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE resume AS "\
                "	SELECT to_char(startdate,'dd Mon YYYY') startdate,to_char(stopdate,'dd Mon YYYY') stopdate,cp.id iup_id, bu.code iup, sub_activity, "\
                "	max(case when item='PLAN' then volume end) Plan, "\
                "	max(case when item='AKTUAL' then volume end) Aktual "\
                "	FROM "\
                "	( "\
                "		SELECT * FROM prod_akt "\
                "		UNION ALL "\
                "		select * from prod_plan "\
                "		UNION ALL "\
                "		select * from hauling_akt "\
                "		UNION ALL "\
                "		select * from hauling_plan "\
                "		UNION ALL "\
                "		select * from barging_akt "\
                "		UNION ALL "\
                "		select * from barging_plan "\
                "	)DATA "\
                "	left join res_company cp on cp.active=true and data.iup=cp.name "\
                "	left join master_bisnis_unit bu on bu.active=true and data.iup=bu.name "\
                "	group by cp.id,bu.code, sub_activity "\
                "	order by sub_activity,iup_id; "\
                "END $$; "\
                "SELECT 'Daily' Data_Remark_Date, "\
                "	RESUME.*, "\
                "	AKTUAL / PLAN ACH,  "\
                "group_notif.LOGIN, "\
                "	CASE WHEN AKTUAL / PLAN < 1 THEN 0 "\
                "	WHEN AKTUAL / PLAN >= 1 THEN 1 "\
                "	ELSE NULL "\
                "	END TIPE, "\
                "	CASE "\
                "	WHEN AKTUAL / PLAN < 1 THEN CONCAT('tidak tercapai') "\
                "	WHEN AKTUAL / PLAN >= 1 THEN CONCAT('all is good') "\
                "	ELSE CONCAT('ERROR') "\
                "	END REMARK, "\
                "group_notif.name Group_Notif "\
                "FROM RESUME "\
                "left join  "\
                "	( "\
                "		select  "\
                "		gr.*,us.login,cp.name company_name,cp.id company_id "\
                "		from res_groups gr "\
                "		left join res_groups_users_rel gru on gr.id=gru.gid "\
                "		left join res_users us on gru.uid=us.id "\
                "		left join res_company_users_rel cus on us.id=cus.user_id  "\
                "		left join res_company cp on cus.cid=cp.id "\
                "		where gr.name='Daily_Group_Notif' "\
                "	)group_notif on group_notif.company_id=resume.iup_id "\
                "where 	 "\
                "	CASE WHEN AKTUAL / PLAN < 1 THEN 0 "\
                "	WHEN AKTUAL / PLAN >= 1 THEN 1 "\
                "	ELSE NULL "\
                "	END is not null "\
                "order by login,iup,sub_activity "
        return query

    def QueryNotifWeekly(self):
        query = "DO $$ "\
                "DECLARE startdate date; stopdate date; activity text; "\
                "BEGIN "\
                "    SELECT date(date_trunc('month', current_date - INTEGER '2')) INTO startdate; "\
                "	SELECT current_date - INTEGER '2' INTO stopdate; "\
                "    DROP TABLE IF EXISTS prod_akt; "\
                "	DROP TABLE IF EXISTS prod_plan; "\
                "    DROP TABLE IF EXISTS hauling_akt; "\
                "	DROP TABLE IF EXISTS hauling_plan; "\
                "	DROP TABLE IF EXISTS barging_akt; "\
                "	DROP TABLE IF EXISTS barging_plan; "\
                "	DROP TABLE IF EXISTS resume; "\
                "    CREATE TABLE prod_akt AS "\
                "    select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	sa.name Sub_Activity, "\
                "	sum(ap.volume) volume "\
                "	 from act_production ap "\
                "	left join master_sub_activity sa on sa.id = ap.sub_activity_id "\
                "	left join res_company cp on ap.bu_company_id = cp.id "\
                "	where  ap.date_act between startdate and stopdate "\
                "	and ap.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "    CREATE TABLE prod_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' Sub_Activity, "\
                "	sa.name, "\
                "	sum(pp.volume_plan) volume "\
                "	 from planning_production pp "\
                "	left join master_sub_activity sa on sa.id = pp.sub_activity_id "\
                "	left join res_company cp on pp.bu_company_id = cp.id "\
                "	where pp.date_START between startdate and stopdate "\
                "	and pp.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE hauling_akt AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' else sa.name end Sub_Activity, "\
                "	sum(ah.volume) volume "\
                "	 from act_hauling ah "\
                "	left join master_sub_activity sa on sa.id = ah.sub_activity_id "\
                "	left join res_company cp on ah.bu_company_id = cp.id "\
                "	where  ah.date_act between startdate and stopdate "\
                "	and ah.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE hauling_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' item, "\
                "	case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' else sa.name end  Sub_Activity, "\
                "	sum(ph.volume_plan) volume "\
                "	 from planning_hauling ph "\
                "	left join master_sub_activity sa on sa.id = ph.sub_activity_id "\
                "	left join res_company cp on ph.bu_company_id = cp.id "\
                "	where ph.date_START between startdate and stopdate "\
                "	and ph.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE barging_akt AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	sa.name Sub_Activity, "\
                "	sum(ab.volume) volume "\
                "	 from act_barging ab "\
                "	left join master_sub_activity sa on sa.id = ab.sub_activity_id "\
                "	left join res_company cp on ab.bu_company_id = cp.id "\
                "	where  ab.date_act between startdate and stopdate "\
                "	and ab.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE barging_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' item, "\
                "	sa.name Sub_Activity, "\
                "	sum(pb.volume_plan) volume "\
                "	 from planning_barging pb "\
                "	left join master_sub_activity sa on sa.id = pb.sub_activity_id "\
                "	left join res_company cp on pb.bu_company_id = cp.id "\
                "	where pb.date_START between startdate and stopdate "\
                "	and pb.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE resume AS "\
                "	SELECT to_char(startdate,'dd Mon YYYY') startdate,to_char(stopdate,'dd Mon YYYY') stopdate,cp.id iup_id, bu.code iup, sub_activity, "\
                "	max(case when item='PLAN' then volume end) Plan, "\
                "	max(case when item='AKTUAL' then volume end) Aktual "\
                "	FROM "\
                "	( "\
                "		SELECT * FROM prod_akt "\
                "		UNION ALL "\
                "		select * from prod_plan "\
                "		UNION ALL "\
                "		select * from hauling_akt "\
                "		UNION ALL "\
                "		select * from hauling_plan "\
                "		UNION ALL "\
                "		select * from barging_akt "\
                "		UNION ALL "\
                "		select * from barging_plan "\
                "	)DATA "\
                "	left join res_company cp on cp.active=true and data.iup=cp.name "\
                "	left join master_bisnis_unit bu on bu.active=true and data.iup=bu.name "\
                "	group by cp.id,bu.code, sub_activity "\
                "	order by sub_activity,iup_id; "\
                "END $$; "\
                "SELECT 'MTD' Data_Remark_Date, "\
                "	RESUME.*, "\
                "	AKTUAL / PLAN ACH, "\
                "group_notif.LOGIN, "\
                "	CASE WHEN AKTUAL / PLAN < 1 THEN 0 "\
                "	WHEN AKTUAL / PLAN >= 1 THEN 1 "\
                "	ELSE NULL "\
                "	END TIPE, "\
                "	CASE "\
                "	WHEN AKTUAL / PLAN < 1 THEN CONCAT('tidak tercapai') "\
                "	WHEN AKTUAL / PLAN >= 1 THEN CONCAT('all is good') "\
                "	ELSE CONCAT('ERROR') "\
                "	END REMARK, "\
                "group_notif.name Group_Notif "\
                "FROM RESUME "\
                "left join  "\
                "	( "\
                "		select  "\
                "		gr.*,us.login,cp.name company_name,cp.id company_id "\
                "		from res_groups gr "\
                "		left join res_groups_users_rel gru on gr.id=gru.gid "\
                "		left join res_users us on gru.uid=us.id "\
                "		left join res_company_users_rel cus on us.id=cus.user_id  "\
                "		left join res_company cp on cus.cid=cp.id "\
                "		where gr.name='Weekly_Group_Notif' "\
                "	)group_notif on group_notif.company_id=resume.iup_id "\
                "where 	 "\
                "	CASE WHEN AKTUAL / PLAN < 1 THEN 0 "\
                "	WHEN AKTUAL / PLAN >= 1 THEN 1 "\
                "	ELSE NULL "\
                "	END is not null "\
                "order by login,iup,sub_activity "
        return query

    def QueryNotifMonthly(self):
        query = "DO $$ "\
                "DECLARE startdate date; stopdate date; activity text; "\
                "BEGIN "\
                "    SELECT date(date_trunc('year', current_date - INTEGER '1')) INTO startdate; "\
                "	SELECT date(date_trunc('month', current_date - INTEGER '1')) - INTEGER '1' INTO stopdate; "\
                "    DROP TABLE IF EXISTS prod_akt; "\
                "	DROP TABLE IF EXISTS prod_plan; "\
                "    DROP TABLE IF EXISTS hauling_akt; "\
                "	DROP TABLE IF EXISTS hauling_plan; "\
                "	DROP TABLE IF EXISTS barging_akt; "\
                "	DROP TABLE IF EXISTS barging_plan; "\
                "	DROP TABLE IF EXISTS resume; "\
                "    CREATE TABLE prod_akt AS "\
                "    select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	sa.name Sub_Activity, "\
                "	sum(ap.volume) volume "\
                "	 from act_production ap "\
                "	left join master_sub_activity sa on sa.id = ap.sub_activity_id "\
                "	left join res_company cp on ap.bu_company_id = cp.id "\
                "	where  ap.date_act between startdate and stopdate "\
                "	and ap.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "    CREATE TABLE prod_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' Sub_Activity, "\
                "	sa.name, "\
                "	sum(pp.volume_plan) volume "\
                "	 from planning_production pp "\
                "	left join master_sub_activity sa on sa.id = pp.sub_activity_id "\
                "	left join res_company cp on pp.bu_company_id = cp.id "\
                "	where pp.date_START between startdate and stopdate "\
                "	and pp.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE hauling_akt AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' else sa.name end Sub_Activity, "\
                "	sum(ah.volume) volume "\
                "	 from act_hauling ah "\
                "	left join master_sub_activity sa on sa.id = ah.sub_activity_id "\
                "	left join res_company cp on ah.bu_company_id = cp.id "\
                "	where  ah.date_act between startdate and stopdate "\
                "	and ah.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE hauling_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' item, "\
                "	case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' else sa.name end  Sub_Activity, "\
                "	sum(ph.volume_plan) volume "\
                "	 from planning_hauling ph "\
                "	left join master_sub_activity sa on sa.id = ph.sub_activity_id "\
                "	left join res_company cp on ph.bu_company_id = cp.id "\
                "	where ph.date_START between startdate and stopdate "\
                "	and ph.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE barging_akt AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'AKTUAL' Item, "\
                "	sa.name Sub_Activity, "\
                "	sum(ab.volume) volume "\
                "	 from act_barging ab "\
                "	left join master_sub_activity sa on sa.id = ab.sub_activity_id "\
                "	left join res_company cp on ab.bu_company_id = cp.id "\
                "	where  ab.date_act between startdate and stopdate "\
                "	and ab.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE barging_plan AS "\
                "	select "\
                "	cp.name IUP, "\
                "	'PLAN' item, "\
                "	sa.name Sub_Activity, "\
                "	sum(pb.volume_plan) volume "\
                "	 from planning_barging pb "\
                "	left join master_sub_activity sa on sa.id = pb.sub_activity_id "\
                "	left join res_company cp on pb.bu_company_id = cp.id "\
                "	where pb.date_START between startdate and stopdate "\
                "	and pb.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name; "\
                "	CREATE TABLE resume AS "\
                "	SELECT to_char(startdate,'dd Mon YYYY') startdate,to_char(stopdate,'dd Mon YYYY') stopdate,cp.id iup_id, bu.code iup, sub_activity, "\
                "	max(case when item='PLAN' then volume end) Plan, "\
                "	max(case when item='AKTUAL' then volume end) Aktual "\
                "	FROM "\
                "	( "\
                "		SELECT * FROM prod_akt "\
                "		UNION ALL "\
                "		select * from prod_plan "\
                "		UNION ALL "\
                "		select * from hauling_akt "\
                "		UNION ALL "\
                "		select * from hauling_plan "\
                "		UNION ALL "\
                "		select * from barging_akt "\
                "		UNION ALL "\
                "		select * from barging_plan "\
                " "\
                "	)DATA "\
                "	left join res_company cp on cp.active=true and data.iup=cp.name "\
                "	left join master_bisnis_unit bu on bu.active=true and data.iup=bu.name "\
                " "\
                "	group by cp.id,bu.code, sub_activity "\
                "	order by sub_activity,iup_id; "\
                " "\
                "END $$; "\
                " "\
                " "\
                "SELECT 'YTD' Data_Remark_Date, "\
                "	RESUME.*, "\
                "	AKTUAL / PLAN ACH, "\
                "group_notif.LOGIN, "\
                "	CASE WHEN AKTUAL / PLAN < 1 THEN 0 "\
                "	WHEN AKTUAL / PLAN >= 1 THEN 1 "\
                "	ELSE NULL "\
                "	END TIPE, "\
                "	CASE "\
                "	WHEN AKTUAL / PLAN < 1 THEN CONCAT('tidak tercapai') "\
                "	WHEN AKTUAL / PLAN >= 1 THEN CONCAT('all is good') "\
                "	ELSE CONCAT('ERROR') "\
                "	END REMARK, "\
                "group_notif.name Group_Notif "\
                "FROM RESUME "\
                "left join  "\
                "	( "\
                "		select  "\
                "		gr.*,us.login,cp.name company_name,cp.id company_id "\
                "		from res_groups gr "\
                "		left join res_groups_users_rel gru on gr.id=gru.gid "\
                "		left join res_users us on gru.uid=us.id "\
                "		left join res_company_users_rel cus on us.id=cus.user_id  "\
                "		left join res_company cp on cus.cid=cp.id "\
                "		where gr.name='Monthly_Group_Notif' "\
                "	)group_notif on group_notif.company_id=resume.iup_id "\
                "where 	 "\
                "	CASE WHEN AKTUAL / PLAN < 1 THEN 0 "\
                "	WHEN AKTUAL / PLAN >= 1 THEN 1 "\
                "	ELSE NULL "\
                "	END is not null "\
                "order by login,iup,sub_activity "
        return query
