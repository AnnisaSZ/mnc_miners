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


class BcrQeuryResume(Exception):

    def QueryTableOverview(self, date, bu_id):
        # date = date.replace("-", "")
        # bu_id = "','".join([str(elem) for elem in bu_id])
        # =================================
        # ==========Update 14 Aug 2023 pada main
        query = '''
            DO $$
            DECLARE tgl date; iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s into iup;

                DROP TABLE IF EXISTS data_aktual_raw;
                DROP TABLE IF EXISTS data_aktual;
                DROP TABLE IF EXISTS data_plan;

                CREATE TABLE data_aktual_raw AS
                select
                'overburden' sub_activity,
                s.name shift,
                sum(ap.volume) act
                 from act_production ap
                left join master_sub_activity sa on sa.id = ap.sub_activity_id
                left join master_shift s on ap.shift_id=s.id
                left join res_company cp on ap.bu_company_id = cp.id
                where ap.date_act = tgl
                and ap.active=TRUE
                and state='complete'
                and sa.name='OVERBURDEN'
                and cp.id = any(iup)
                group by sa.name,s.name 

                union all

                select 
                'coal_getting' sub_activity,
                s.name shift,
                sum(ap.volume) act
                 from act_production ap
                left join master_sub_activity sa on sa.id = ap.sub_activity_id
                left join master_shift s on ap.shift_id=s.id
                left join res_company cp on ap.bu_company_id = cp.id
                where ap.date_act = tgl
                and ap.active=TRUE
                and state='complete'
                and sa.name='COAL GETTING'
                and cp.id = any(iup)
                group by sa.name,s.name 

                union all

                select 
                'coal_hauling' sub_activity,
                s.name shift,
                sum(ah.volume) act
                 from act_hauling ah
                left join master_sub_activity sa on sa.id = ah.sub_activity_id
                left join master_shift s on ah.shift_id=s.id
                left join res_company cp on ah.bu_company_id = cp.id
                where ah.date_act = tgl
                and ah.active=TRUE
                and state='complete'
                and cp.id = any(iup)
                group by sa.name,s.name 

                union all

                select 'rain_slippery' sub_activity, shift,sum(total) total
                from
                    (
                    select 
                    d.date_act date,
                    pt.name Keterangan,
                    s.name Shift, avg(d.volume) Total 
                    from act_delay d
                    left join res_company cp on d.bu_company_id=cp.id
                    left join product_product pp on pp.id=d.product
                    left join product_template pt on pt.id=pp.product_tmpl_id
                    left join master_shift s on d.shift_id=s.id
                    where d.date_act = tgl
                    and pt.name in ('RAIN','SLIPPERY')
                    and cp.id = any(iup)
                    group by 
                    pt.name,
                    s.name,
                    d.date_act
                    order by date_act,shift
                    )rsdetail
                group by shift

                union all

                select 
                'coal_barging' sub_activity,
                s.name shift,
                sum(ab.volume) act
                 from act_barging ab
                left join master_sub_activity sa on sa.id = ab.sub_activity_id
                left join master_shift s on ab.shift_id=s.id
                left join res_company cp on ab.bu_company_id = cp.id
                where ab.date_act = tgl
                and ab.active=TRUE
                and ab.state='complete'
                and cp.id = any(iup)
                group by sa.name,s.name 
                ;
                
                
                CREATE TABLE data_aktual AS 

            select 
            shift item, 
            sum(case when sub_activity = 'overburden' then act end) overburden,
            sum(case when sub_activity = 'coal_getting' then act end) coal_getting,
            sum(case when sub_activity = 'overburden' then act end)/nullif(sum(case when sub_activity = 'coal_getting' then act end),0) SR,
            sum(case when sub_activity = 'rain_slippery' then act end) rain_slippery,
            sum(case when sub_activity = 'coal_hauling' then act end) coal_hauling,
            sum(case when sub_activity = 'coal_barging' then act end) coal_barging
             from data_aktual_raw
            group by shift
            order by shift
            ;


                CREATE TABLE data_plan AS   
                select 
                ob.item,
                ob.act overburden,
                coal.act coal_getting,
                ob.act/nullif(coal.act,0) SR,
                rs.total rain_slippery,
                ch.act coal_hauling,
                barg.act coal_Barging
                from 

                (
                select 
                'PLAN' item,
                sum(pp.volume_plan) act
                 from planning_production pp
                left join master_sub_activity sa on sa.id = pp.sub_activity_id
                left join res_company cp on pp.bu_company_id = cp.id
                where pp.date_start = tgl
                and pp.active=TRUE
                and state='complete'
                and sa.name='OVERBURDEN'
                and cp.id = any(iup)
                )ob

                left join
                (
                select 
                'PLAN' item,
                sum(pp.volume_plan) act
                 from planning_production pp
                left join master_sub_activity sa on sa.id = pp.sub_activity_id
                left join res_company cp on pp.bu_company_id = cp.id
                where pp.date_start = tgl
                and pp.active=TRUE
                and state='complete'
                and sa.name='COAL GETTING'
                and cp.id = any(iup)
                )coal
                on ob.item=coal.item

                left join
                (
                select 
                'PLAN' item,
                sum(ph.volume_plan) act
                 from planning_hauling ph
                left join master_sub_activity sa on sa.id = ph.sub_activity_id
                left join res_company cp on ph.bu_company_id = cp.id
                where ph.date_start = tgl
                and ph.active=TRUE
                and state='complete'
                and cp.id = any(iup)
                )ch
                on ob.item=ch.item

                left join
                (select
                date date,
                'PLAN' item,
                0.00 total
                from
                (
                select 
                d.date_act date,
                --pt.name Keterangan,
                s.name Shift, avg(d.volume) Total 
                from act_delay d
                left join res_company cp on d.bu_company_id=cp.id
                left join product_product pp on pp.id=d.product
                left join product_template pt on pt.id=pp.product_tmpl_id
                left join master_shift s on d.shift_id=s.id
                where d.date_act = tgl
                and pt.name in ('RAIN','SLIPPERY')
                and d.active=TRUE
                and d.state='complete'
                and cp.id = any(iup)
                group by 
                --pt.name,
                s.name,
                d.date_act
                order by date_act,shift
                )data
                group by date
                )rs on ob.item=rs.item

                left join
                (
                select 
                'PLAN' item,
                sum(pb.volume_plan) act
                 from planning_barging pb
                left join master_sub_activity sa on sa.id = pb.sub_activity_id
                left join res_company cp on pb.bu_company_id = cp.id
                where pb.date_start = tgl
                and pb.active=TRUE
                and pb.state='complete'
                and cp.id = any(iup)
                )barg
                on ob.item=barg.item
                ;


            end$$;

            select * from data_aktual

            union all

            select 
            'AKTUAL' items, 
            sum(overburden) overburden,
            sum(coal_getting) coal_getting, 
            sum(overburden)/nullif(sum(coal_getting),0) SR,
            sum(rain_slippery) rain_slippery,
            sum(coal_hauling) coal_hauling,
            sum(coal_barging) coal_barging
            from data_aktual
            group by items

            union all

            select * from data_plan

            union all

            select 
            'ACH' itemss,
            a.overburden/nullif(p.overburden,0) overburden,
            a.coal_getting/nullif(p.coal_getting,0) coal_getting,
            p.sr/nullif(a.sr,0) sr,
            a.rain_slippery/nullif(p.rain_slippery,0) rain_slippery,
            a.coal_hauling/nullif(p.coal_hauling,0) coal_hauling,
            a.coal_barging/nullif(p.coal_barging,0) coal_barging

             from (
            select 
            'AKTUAL' items, 
            sum(overburden) overburden,
            sum(coal_getting) coal_getting, 
            sum(overburden)/nullif(sum(coal_getting),0) SR,
            sum(rain_slippery) rain_slippery,
            sum(coal_hauling) coal_hauling,
            sum(coal_barging) coal_barging
            from data_aktual
            group by items)a
            left join
            (select 'AKTUAL' items,
            sum(overburden) overburden,
            sum(coal_getting) coal_getting, 
            sum(overburden)/nullif(sum(coal_getting),0) SR,
            sum(rain_slippery) rain_slippery,
            sum(coal_hauling) coal_hauling,
            sum(coal_barging) coal_barging
             from data_plan group by items) p
            on a.items=p.items
        ''' % (date, bu_id)
        return query
        # ==========Update 4 Aug 2023 pada main
        # query = '''
        #     DO $$
        #     DECLARE tgl date; iup integer;

        #     BEGIN
        #         SELECT '%s' INTO tgl;
        #         SELECT '%s' INTO iup;

        #         DROP TABLE IF EXISTS data_aktual_raw;
        #         DROP TABLE IF EXISTS data_aktual;
        #         DROP TABLE IF EXISTS data_plan;
                
        #         CREATE TABLE data_aktual_raw AS
        #         select 
        #         'overburden' sub_activity,
        #         s.name shift,
        #         sum(ap.volume) act
        #          from act_production ap
        #         left join master_sub_activity sa on sa.id = ap.sub_activity_id
        #         left join master_shift s on ap.shift_id=s.id
        #         left join res_company cp on ap.bu_company_id = cp.id
        #         where ap.date_act = tgl
        #         and ap.active=TRUE
        #         and state='complete'
        #         and sa.name='OVERBURDEN'
        #         and cp.id in (iup)
        #         group by sa.name,s.name 

        #         union all

        #         select 
        #         'coal_getting' sub_activity,
        #         s.name shift,
        #         sum(ap.volume) act
        #          from act_production ap
        #         left join master_sub_activity sa on sa.id = ap.sub_activity_id
        #         left join master_shift s on ap.shift_id=s.id
        #         left join res_company cp on ap.bu_company_id = cp.id
        #         where ap.date_act = tgl
        #         and ap.active=TRUE
        #         and state='complete'
        #         and sa.name='COAL GETTING'
        #         and cp.id in (iup)
        #         group by sa.name,s.name 

        #         union all

        #         select 
        #         'coal_hauling' sub_activity,
        #         s.name shift,
        #         sum(ah.volume) act
        #          from act_hauling ah
        #         left join master_sub_activity sa on sa.id = ah.sub_activity_id
        #         left join master_shift s on ah.shift_id=s.id
        #         left join res_company cp on ah.bu_company_id = cp.id
        #         where ah.date_act = tgl
        #         and ah.active=TRUE
        #         and state='complete'
        #         and cp.id in (iup)
        #         group by sa.name,s.name 

        #         union all

        #         select 'rain_slippery' sub_activity, shift,sum(total) total
        #         from
        #             (
        #             select 
        #             d.date_act date,
        #             pt.name Keterangan,
        #             s.name Shift, avg(d.volume) Total 
        #             from act_delay d
        #             left join res_company cp on d.bu_company_id=cp.id
        #             left join product_product pp on pp.id=d.product
        #             left join product_template pt on pt.id=pp.product_tmpl_id
        #             left join master_shift s on d.shift_id=s.id
        #             where d.date_act = tgl
        #             and pt.name in ('RAIN','SLIPPERY')
        #             and cp.id in (iup)
        #             group by 
        #             pt.name,
        #             s.name,
        #             d.date_act
        #             order by date_act,shift
        #             )rsdetail
        #         group by shift

        #         union all

        #         select 
        #         'coal_barging' sub_activity,
        #         s.name shift,
        #         sum(ab.volume) act
        #          from act_barging ab
        #         left join master_sub_activity sa on sa.id = ab.sub_activity_id
        #         left join master_shift s on ab.shift_id=s.id
        #         left join res_company cp on ab.bu_company_id = cp.id
        #         where ab.date_act = tgl
        #         and ab.active=TRUE
        #         and ab.state='complete'
        #         and cp.id in (iup)
        #         group by sa.name,s.name 
        #         ;
                
                
        #         CREATE TABLE data_aktual AS 

        #     select 
        #     shift item, 
        #     sum(case when sub_activity = 'overburden' then act end) overburden,
        #     sum(case when sub_activity = 'coal_getting' then act end) coal_getting,
        #     sum(case when sub_activity = 'overburden' then act end)/nullif(sum(case when sub_activity = 'coal_getting' then act end),0) SR,
        #     sum(case when sub_activity = 'rain_slippery' then act end) rain_slippery,
        #     sum(case when sub_activity = 'coal_hauling' then act end) coal_hauling,
        #     sum(case when sub_activity = 'coal_barging' then act end) coal_barging
        #      from data_aktual_raw
        #     group by shift
        #     order by shift
        #     ;


        #         CREATE TABLE data_plan AS   
        #         select 
        #         ob.item,
        #         ob.act overburden,
        #         coal.act coal_getting,
        #         ob.act/nullif(coal.act,0) SR,
        #         rs.total rain_slippery,
        #         ch.act coal_hauling,
        #         barg.act coal_Barging
        #         from 

        #         (
        #         select 
        #         'PLAN' item,
        #         sum(pp.volume_plan) act
        #          from planning_production pp
        #         left join master_sub_activity sa on sa.id = pp.sub_activity_id
        #         left join res_company cp on pp.bu_company_id = cp.id
        #         where pp.date_start = tgl
        #         and pp.active=TRUE
        #         and state='complete'
        #         and sa.name='OVERBURDEN'
        #         and cp.id in (iup)
        #         )ob

        #         left join
        #         (
        #         select 
        #         'PLAN' item,
        #         sum(pp.volume_plan) act
        #          from planning_production pp
        #         left join master_sub_activity sa on sa.id = pp.sub_activity_id
        #         left join res_company cp on pp.bu_company_id = cp.id
        #         where pp.date_start = tgl
        #         and pp.active=TRUE
        #         and state='complete'
        #         and sa.name='COAL GETTING'
        #         and cp.id in (iup)
        #         )coal
        #         on ob.item=coal.item

        #         left join
        #         (
        #         select 
        #         'PLAN' item,
        #         sum(ph.volume_plan) act
        #          from planning_hauling ph
        #         left join master_sub_activity sa on sa.id = ph.sub_activity_id
        #         left join res_company cp on ph.bu_company_id = cp.id
        #         where ph.date_start = tgl
        #         and ph.active=TRUE
        #         and state='complete'
        #         and cp.id in (iup)
        #         )ch
        #         on ob.item=ch.item

        #         left join
        #         (select
        #         date date,
        #         'PLAN' item,
        #         0.00 total
        #         from
        #         (
        #         select 
        #         d.date_act date,
        #         --pt.name Keterangan,
        #         s.name Shift, avg(d.volume) Total 
        #         from act_delay d
        #         left join res_company cp on d.bu_company_id=cp.id
        #         left join product_product pp on pp.id=d.product
        #         left join product_template pt on pt.id=pp.product_tmpl_id
        #         left join master_shift s on d.shift_id=s.id
        #         where d.date_act = tgl
        #         and pt.name in ('RAIN','SLIPPERY')
        #         and d.active=TRUE
        #         and d.state='complete'
        #         and cp.id in (iup)
        #         group by 
        #         --pt.name,
        #         s.name,
        #         d.date_act
        #         order by date_act,shift
        #         )data
        #         group by date
        #         )rs on ob.item=rs.item

        #         left join
        #         (
        #         select 
        #         'PLAN' item,
        #         sum(pb.volume_plan) act
        #          from planning_barging pb
        #         left join master_sub_activity sa on sa.id = pb.sub_activity_id
        #         left join res_company cp on pb.bu_company_id = cp.id
        #         where pb.date_start = tgl
        #         and pb.active=TRUE
        #         and pb.state='complete'
        #         and cp.id in (iup)
        #         )barg
        #         on ob.item=barg.item
        #         ;


        #     end$$;

        #     select * from data_aktual

        #     union all

        #     select 
        #     'AKTUAL' items, 
        #     sum(overburden) overburden,
        #     sum(coal_getting) coal_getting, 
        #     sum(overburden)/nullif(sum(coal_getting),0) SR,
        #     sum(rain_slippery) rain_slippery,
        #     sum(coal_hauling) coal_hauling,
        #     sum(coal_barging) coal_barging
        #     from data_aktual
        #     group by items

        #     union all

        #     select * from data_plan

        #     union all

        #     select 
        #     'ACH' itemss,
        #     a.overburden/nullif(p.overburden,0) overburden,
        #     a.coal_getting/nullif(p.coal_getting,0) coal_getting,
        #     p.sr/nullif(a.sr,0) sr,
        #     a.rain_slippery/nullif(p.rain_slippery,0) rain_slippery,
        #     a.coal_hauling/nullif(p.coal_hauling,0) coal_hauling,
        #     a.coal_barging/nullif(p.coal_barging,0) coal_barging

        #      from (
        #     select 
        #     'AKTUAL' items, 
        #     sum(overburden) overburden,
        #     sum(coal_getting) coal_getting, 
        #     sum(overburden)/nullif(sum(coal_getting),0) SR,
        #     sum(rain_slippery) rain_slippery,
        #     sum(coal_hauling) coal_hauling,
        #     sum(coal_barging) coal_barging
        #     from data_aktual
        #     group by items)a
        #     left join
        #     (select 'AKTUAL' items,
        #     sum(overburden) overburden,
        #     sum(coal_getting) coal_getting, 
        #     sum(overburden)/nullif(sum(coal_getting),0) SR,
        #     sum(rain_slippery) rain_slippery,
        #     sum(coal_hauling) coal_hauling,
        #     sum(coal_barging) coal_barging
        #      from data_plan group by items) p
        #     on a.items=p.items
        # ''' % (date, bu_id)
        # =================================
        # query = "DO $$ DECLARE tgl date;iup integer[]; " \
        #         "BEGIN " \
        #         "SELECT " \
        #         "  '"+date+"' INTO tgl;" \
        #         "SELECT " \
        #         "  ARRAY['"+str(bu_id)+"'] INTO iup;" \
        #         "DROP " \
        #         "  TABLE IF EXISTS data_aktual;" \
        #         "DROP " \
        #         "  TABLE IF EXISTS data_plan;" \
        #         "CREATE TABLE data_aktual AS " \
        #         "select " \
        #         "  ob.shift item, " \
        #         "  ob.act overburden, " \
        #         "  coal.act coal_getting, " \
        #         "  ob.act / nullif(coal.act, 0) SR, " \
        #         "  case when rs.total isnull then 0 else rs.total end Rain_Slippery, " \
        #         "  ch.act coal_hauling, " \
        #         "  barg.act coal_Barging " \
        #         "  from " \
        #         "  (" \
        #         "    select " \
        #         "      s.name shift, " \
        #         "      sum(ap.volume) act " \
        #         "    from " \
        #         "      act_production ap " \
        #         "           left join master_sub_activity sa on sa.id = ap.sub_activity_id " \
        #         "      left join master_shift s on ap.shift_id = s.id " \
        #         "      left join res_company cp on ap.bu_company_id = cp.id " \
        #         "    where " \
        #         "      ap.date_act = tgl " \
        #         "      and ap.active = TRUE " \
        #         "            and state = 'complete' " \
        #         "      and sa.name = 'OVERBURDEN' " \
        #         "      and cp.id = any(iup) " \
        #         "    group by " \
        #         "      sa.name, " \
        #         "      s.name" \
        #         "  ) ob " \
        #         "  left join ( " \
        #         "            select " \
        #         "      s.name shift, " \
        #         "      sum(ap.volume) act " \
        #         "            from " \
        #         "      act_production ap " \
        #         "      left join master_sub_activity sa on sa.id = ap.sub_activity_id " \
        #         "      left join master_shift s on ap.shift_id = s.id " \
        #         "      left join res_company cp on ap.bu_company_id = cp.id " \
        #         "    where " \
        #         "      ap.date_act = tgl " \
        #         "      and ap.active = TRUE " \
        #         "      and state = 'complete' " \
        #         "      and sa.name = 'COAL GETTING' " \
        #         "      and cp.id = any(iup) " \
        #         "    group by " \
        #         "      sa.name, " \
        #         "      s.name" \
        #         "  ) coal on ob.shift = coal.shift " \
        #         "  left join (" \
        #         "    select " \
        #         "      s.name shift, " \
        #         "      sum(ah.volume) act " \
        #         "    from " \
        #         "      act_hauling ah " \
        #         "      left join master_sub_activity sa on sa.id = ah.sub_activity_id " \
        #         "      left join master_shift s on ah.shift_id = s.id " \
        #         "      left join res_company cp on ah.bu_company_id = cp.id " \
        #         "    where " \
        #         "      ah.date_act = tgl " \
        #         "      and ah.active = TRUE " \
        #         "      and state = 'complete' " \
        #         "      and cp.id = any(iup) " \
        #         "    group by " \
        #         "      sa.name, " \
        #         "      s.name" \
        #         "  ) ch on ob.shift = ch.shift " \
        #         "  left join (" \
        #         "    select " \
        #         "      date, " \
        #         "      shift, " \
        #         "      sum(total) total " \
        #         "    from " \
        #         "      (" \
        #         "        select " \
        #         "          d.date_act date, " \
        #         "          pt.name Keterangan, " \
        #         "          s.name Shift, " \
        #         "          avg(d.volume) Total " \
        #         "        from " \
        #         "          act_delay d " \
        #         "          left join res_company cp on d.bu_company_id = cp.id " \
        #         "          left join product_product pp on pp.id = d.product " \
        #         "          left join product_template pt on pt.id = pp.product_tmpl_id " \
        #         "          left join master_shift s on d.shift_id = s.id " \
        #         "        where " \
        #         "          d.date_act = tgl " \
        #         "          and pt.name in ('RAIN', 'SLIPPERY') " \
        #         "          and cp.id = any(iup) " \
        #         "        group by " \
        #         "          pt.name, " \
        #         "          s.name, " \
        #         "          d.date_act " \
        #         "        order by " \
        #         "          date_act, " \
        #         "          shift" \
        #         "      ) rsdetail " \
        #         "    group by " \
        #         "      date, " \
        #         "      shift" \
        #         "  ) rs on ob.shift = rs.shift " \
        #         "  left join ( " \
        #         "      select " \
        #         "      s.name shift, " \
        #         "      sum(ab.volume) act " \
        #         "    from " \
        #         "      act_barging ab " \
        #         "      left join master_sub_activity sa on sa.id = ab.sub_activity_id " \
        #         "      left join master_shift s on ab.shift_id = s.id " \
        #         "      left join res_company cp on ab.bu_company_id = cp.id " \
        #         "    where " \
        #         "      ab.date_act = tgl " \
        #         "      and ab.active = TRUE " \
        #         "      and ab.state = 'complete' " \
        #         "      and cp.id = any(iup) " \
        #         "    group by " \
        #         "      sa.name, " \
        #         "      s.name" \
        #         "  ) barg on barg.shift = ob.shift " \
        #         "order by " \
        #         "  item;" \
        #         "CREATE TABLE data_plan AS " \
        #         "select " \
        #         "  ob.item, " \
        #         "  ob.act overburden, " \
        #         "  coal.act coal_getting, " \
        #         "  ob.act / nullif(coal.act, 0) SR, " \
        #         "  rs.total RS, " \
        #         "  ch.act coal_hauling, " \
        #         "  barg.act Barging " \
        #         "from " \
        #         "  (" \
        #         "    select " \
        #         "      'PLAN' item, " \
        #         "      sum(pp.volume_plan) act " \
        #         "    from " \
        #         "      planning_production pp " \
        #         "      left join master_sub_activity sa on sa.id = pp.sub_activity_id " \
        #         "      left join res_company cp on pp.bu_company_id = cp.id " \
        #         "    where " \
        #         "      pp.date_start = tgl " \
        #         "      and pp.active = TRUE " \
        #         "      and state = 'complete' " \
        #         "      and sa.name = 'OVERBURDEN' " \
        #         "      and cp.id = any(iup)" \
        #         "  ) ob " \
        #         "  left join (" \
        #         "    select " \
        #         "      'PLAN' item, " \
        #         "      sum(pp.volume_plan) act " \
        #         "    from " \
        #         "      planning_production pp " \
        #         "      left join master_sub_activity sa on sa.id = pp.sub_activity_id " \
        #         "      left join res_company cp on pp.bu_company_id = cp.id " \
        #         "    where " \
        #         "      pp.date_start = tgl " \
        #         "      and pp.active = TRUE " \
        #         "      and state = 'complete' " \
        #         "      and sa.name = 'COAL GETTING' " \
        #         "      and cp.id = any(iup)" \
        #         "  ) coal on ob.item = coal.item " \
        #         "  left join (" \
        #         "    select " \
        #         "      'PLAN' item, " \
        #         "      sum(ph.volume_plan) act " \
        #         "    from " \
        #         "      planning_hauling ph " \
        #         "      left join master_sub_activity sa on sa.id = ph.sub_activity_id " \
        #         "      left join res_company cp on ph.bu_company_id = cp.id " \
        #         "    where " \
        #         "      ph.date_start = tgl " \
        #         "      and ph.active = TRUE " \
        #         "      and state = 'complete' " \
        #         "      and cp.id = any(iup)" \
        #         "  ) ch on ob.item = ch.item " \
        #         "  left join (" \
        #         "    select " \
        #         "      date date, " \
        #         "      'PLAN' item, " \
        #         "      0.00 total " \
        #         "    from " \
        #         "      (" \
        #         "        select " \
        #         "          d.date_act date, " \
        #         "          s.name Shift, " \
        #         "          avg(d.volume) Total " \
        #         "        from " \
        #         "          act_delay d " \
        #         "          left join res_company cp on d.bu_company_id = cp.id " \
        #         "          left join product_product pp on pp.id = d.product " \
        #         "          left join product_template pt on pt.id = pp.product_tmpl_id " \
        #         "          left join master_shift s on d.shift_id = s.id " \
        #         "        where " \
        #         "          d.date_act = tgl " \
        #         "          and pt.name in ('RAIN', 'SLIPPERY') " \
        #         "          and d.active = TRUE " \
        #         "          and d.state = 'complete' " \
        #         "          and cp.id = any(iup) " \
        #         "        group by " \
        #         "          s.name, " \
        #         "          d.date_act " \
        #         "        order by " \
        #         "          date_act, " \
        #         "          shift" \
        #         "      ) data " \
        #         "    group by " \
        #         "      date" \
        #         "  ) rs on ob.item = rs.item " \
        #         "  left join (" \
        #         "    select " \
        #         "      'PLAN' item, " \
        #         "      sum(pb.volume_plan) act " \
        #         "    from " \
        #         "      planning_barging pb " \
        #         "      left join master_sub_activity sa on sa.id = pb.sub_activity_id " \
        #         "      left join res_company cp on pb.bu_company_id = cp.id " \
        #         "    where " \
        #         "      pb.date_start = tgl " \
        #         "      and pb.active = TRUE " \
        #         "      and pb.state = 'complete' " \
        #         "      and cp.id = any(iup)" \
        #         "  ) barg on ob.item = barg.item;" \
        #         "end $$;" \
        #         "select " \
        #         "  * " \
        #         "from " \
        #         "  data_aktual " \
        #         "union all " \
        #         "select " \
        #         "  'AKTUAL' item, " \
        #         "  sum(overburden), " \
        #         "  sum(coal_getting), " \
        #         "  sum(overburden) / nullif(" \
        #         "    sum(coal_getting), " \
        #         "    0" \
        #         "  ) SR, " \
        #         "  sum(rain_slippery), " \
        #         "  sum(coal_hauling), " \
        #         "  sum(coal_barging) " \
        #         "from " \
        #         "  data_aktual " \
        #         "union all " \
        #         "select " \
        #         "  * " \
        #         "from " \
        #         "  data_plan " \
        #         "union all " \
        #         "SELECT " \
        #         "  'ACH' item, " \
        #         "  data_aktual.overburden / nullif(data_plan.overburden, 0) OB_ach, " \
        #         "  data_aktual.coal_getting / nullif(data_plan.coal_getting, 0) CG_ach, " \
        #         "  data_plan.SR / nullif(data_aktual.SR, 0) SR_ach, " \
        #         "  data_aktual.rain_slippery / nullif(data_plan.RS, 0) RS_ach, " \
        #         "  data_aktual.coal_hauling / nullif(data_plan.coal_hauling, 0) CH_ach, " \
        #         "  data_aktual.coal_barging / nullif(data_plan.barging, 0) CB_ach " \
        #         "FROM " \
        #         "  DATA_PLAN " \
        #         "  LEFT JOIN (" \
        #         "    select " \
        #         "      'PLAN' item, " \
        #         "      sum(a.overburden) overburden, " \
        #         "      sum(a.coal_getting) coal_getting, " \
        #         "      sum(a.overburden) / sum(a.coal_getting) SR, " \
        #         "      sum(a.rain_slippery) rain_slippery, " \
        #         "      sum(a.coal_hauling) coal_hauling, " \
        #         "      sum(a.coal_barging) coal_barging " \
        #         "    FROM " \
        #         "      DATA_AKTUAL a" \
        #         "  ) DATA_AKTUAL on DATA_AKTUAL.ITEM = DATA_PLAN.ITEM"
        # query = "select ob.shift item,ob.act overburden,coal.act coal_getting,ob.act/coal.act SR,case when rs.total isnull then 0 else rs.total end Rain_Slippery,ch.act coal_hauling,barg.act coal_Barging" \
        #         " from (select s.name shift,sum(ap.volume) act from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join master_shift s on ap.shift_id=s.id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where ap.date_act = '"+date+"' and ap.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"' group by sa.name,s.name )ob left join(select s.name shift,sum(ap.volume) act from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join master_shift s on ap.shift_id=s.id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where ap.date_act = '"+date+"' and ap.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"' group by sa.name,s.name )coal on ob.shift=coal.shift left join(select s.name shift,sum(ah.volume) act " \
        #         " from act_hauling ah left join master_sub_activity sa on sa.id = ah.sub_activity_id left join master_shift s on ah.shift_id=s.id left join res_company cp on ah.bu_company_id = cp.id where ah.date_act = '"+date+"' and ah.active=TRUE and state='complete' and cp.id='"+bu_id+"' group by sa.name,s.name )ch on ob.shift=ch.shift " \
        #         " left join(select date,shift,sum(total) total" \
        #         " from(select d.date_act date,pt.name Keterangan,s.name Shift, avg(d.volume) Total " \
        #         " from act_delay d left join res_company cp on d.bu_company_id=cp.id left join product_product pp on pp.id=d.product left join product_template pt on pt.id=pp.product_tmpl_id left join master_shift s on d.shift_id=s.id " \
        #         " where d.date_act = '"+date+"' and pt.name in ('RAIN','SLIPPERY') and cp.id='"+bu_id+"' group by pt.name,s.name,d.date_act order by date_act,shift)rsdetail group by date,shift)rs on ob.shift=rs.shift" \
        #         " left join (select s.name shift,sum(ab.volume) act" \
        #         " from act_barging ab left join master_sub_activity sa on sa.id = ab.sub_activity_id left join master_shift s on ab.shift_id=s.id left join res_company cp on ab.bu_company_id = cp.id" \
        #         " where ab.date_act = '"+date+"' and ab.active=TRUE and ab.state='complete' and cp.id='"+bu_id+"' group by sa.name,s.name )barg on barg.shift=ob.shift" \
        #         " union all " \
        #         " select ob.shift item,ob.act overburden,coal.act coal_getting,ob.act/coal.act,case when rs.total isnull then 0 else rs.total end,ch.act coal_hauling,barg.act coal_Barging from (select 'AKTUAL' shift,sum(ap.volume) act from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id " \
        #         " where ap.date_act = '"+date+"' and ap.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"')ob" \
        #         " left join(select 'AKTUAL' shift,sum(ap.volume) act from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id " \
        #         " where ap.date_act = '"+date+"' and ap.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"')coal on ob.shift=coal.shift " \
        #         " left join(select 'AKTUAL' shift,sum(ah.volume) act " \
        #         " from act_hauling ah left join master_sub_activity sa on sa.id = ah.sub_activity_id left join res_company cp on ah.bu_company_id = cp.id " \
        #         " where ah.date_act = '"+date+"' and ah.active=TRUE and state='complete' and cp.id='"+bu_id+"' group by sa.name)ch on ob.shift=ch.shift " \
        #         " left join(select date,'AKTUAL' shift, sum(total) total from(select d.date_act date,pt.name Keterangan,s.name Shift, avg(d.volume) Total " \
        #         " from act_delay d left join res_company cp on d.bu_company_id=cp.id left join product_product pp on pp.id=d.product left join product_template pt on pt.id=pp.product_tmpl_id left join master_shift s on d.shift_id=s.id " \
        #         " where d.date_act = '"+date+"' and pt.name in ('RAIN','SLIPPERY') and cp.id='"+bu_id+"' group by pt.name,s.name,d.date_act order by date_act,shift)rsdetail group by date)rs on ob.shift=rs.shift " \
        #         " left join (select 'AKTUAL' shift,sum(ab.volume) act " \
        #         " from act_barging ab left join master_sub_activity sa on sa.id = ab.sub_activity_id left join master_shift s on ab.shift_id=s.id " \
        #         " left join res_company cp on ab.bu_company_id = cp.id where ab.date_act = '"+date+"' " \
        #         " and ab.active=TRUE and ab.state='complete' and cp.id='"+bu_id+"' group by sa.name)barg on barg.shift=ob.shift" \
        #         " union all " \
        #         " select ob.item,ob.act overburden,coal.act coal_getting,ob.act/coal.act,rs.total ,ch.act coal_hauling,barg.act Bargin " \
        #         " from (select 'PLAN' item,sum(pp.volume_plan) act " \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_start = '"+date+"' and pp.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"')ob " \
        #         " left join(select 'PLAN' item,sum(pp.volume_plan) act " \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_start = '"+date+"' and pp.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"')coal on ob.item=coal.item" \
        #         " left join(select 'PLAN' item,sum(ph.volume_plan) act" \
        #         " from planning_hauling ph left join master_sub_activity sa on sa.id = ph.sub_activity_id left join res_company cp on ph.bu_company_id = cp.id " \
        #         " where ph.date_start = '"+date+"' and ph.active=TRUE and state='complete' and cp.id='"+bu_id+"')ch on ob.item=ch.item " \
        #         " left join(select date date,'PLAN' item,0 total from(select d.date_act date,s.name Shift, avg(d.volume) Total " \
        #         " from act_delay d left join res_company cp on d.bu_company_id=cp.id left join product_product pp on pp.id=d.product left join product_template pt on pt.id=pp.product_tmpl_id left join master_shift s on d.shift_id=s.id " \
        #         " where d.date_act = '"+date+"' and pt.name in ('RAIN','SLIPPERY') and d.active=TRUE and d.state='complete' and cp.id='"+bu_id+"' group by s.name,d.date_act order by date_act,shift)data group by date)rs on ob.item=rs.item " \
        #         " left join(select 'PLAN' item,sum(pb.volume_plan) act from planning_barging pb left join master_sub_activity sa on sa.id = pb.sub_activity_id left join res_company cp on pb.bu_company_id = cp.id " \
        #         " where pb.date_start = '"+date+"' and pb.active=TRUE and pb.state='complete' and cp.id='"+bu_id+"')barg on ob.item=barg.item " \
        #         " union all select 'ACH' Item,dataaktual.overburden/dataplan.overburden Ach_OB,dataaktual.coal_getting/dataplan.coal_getting Ach_Coal_Getting,dataplan.stripping/dataaktual.stripping_ratio Ach_SR,dataplan.rain/dataaktual.rain Ach_Rain,dataaktual.coal_hauling/dataplan.coal_hauling Ach_Coal_Hauling,dataaktual.barging/dataplan.barging Ach_Barging " \
        #         " from(select ob.item,ob.act overburden,coal.act coal_getting,ch.act coal_hauling,ob.act/coal.act stripping,rs.total rain,barg.act barging " \
        #         " from(select 'Value' item,sum(pp.volume_plan) act " \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_start = '"+date+"' and pp.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"')ob " \
        #         " left join(select'Value' item,sum(pp.volume_plan) act " \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id " \
        #         " left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_start = '"+date+"' and pp.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"')coal on ob.item=coal.item " \
        #         " left join(select 'Value' item,sum(ph.volume_plan) act " \
        #         " from planning_hauling ph left join master_sub_activity sa on sa.id = ph.sub_activity_id left join res_company cp on ph.bu_company_id = cp.id " \
        #         " where ph.date_start = '"+date+"' and ph.active=TRUE and state='complete' and cp.id='"+bu_id+"')ch on ob.item=ch.item " \
        #         " left join (select date date,'Value' item,0 total " \
        #         " from(select d.date_act date,s.name Shift, avg(d.volume) Total from act_delay d left join res_company cp on d.bu_company_id=cp.id left join product_product pp on pp.id=d.product left join product_template pt on pt.id=pp.product_tmpl_id left join master_shift s on d.shift_id=s.id " \
        #         " where d.date_act = '"+date+"' and pt.name in ('RAIN','SLIPPERY') and d.active=TRUE and d.state='complete' and cp.id='"+bu_id+"' group by s.name,d.date_act order by date_act,shift)data group by date)rs on ob.item=rs.item " \
        #         " left join(select 'Value' item,sum(pb.volume_plan) act" \
        #         " from planning_barging pb left join master_sub_activity sa on sa.id = pb.sub_activity_id left join res_company cp on pb.bu_company_id = cp.id " \
        #         " where pb.date_start = '"+date+"' and pb.active=TRUE and pb.state='complete' and cp.id='"+bu_id+"')barg on ob.item=barg.item)dataplan " \
        #         " left join(select ob.item item,ob.act overburden,coal.act coal_getting,ch.act coal_hauling,ob.act/coal.act Stripping_Ratio,rs.total rain,barg.act barging " \
        #         " from (select 'Value' item,sum(ap.volume) act " \
        #         " from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id " \
        #         " where ap.date_act = '"+date+"' and ap.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"')ob " \
        #         " left join(select 'Value' item,sum(ap.volume) act " \
        #         " from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id " \
        #         " where ap.date_act = '"+date+"' and ap.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"')coal on ob.item=coal.item " \
        #         " left join(select 'Value' item,sum(ah.volume) act " \
        #         " from act_hauling ah left join master_sub_activity sa on sa.id = ah.sub_activity_id left join res_company cp on ah.bu_company_id = cp.id " \
        #         " where ah.date_act = '"+date+"' and ah.active=TRUE and state='complete')ch on ob.item=ch.item " \
        #         " left join (select 'Value' item, sum(total) total from(select d.date_act date,pt.name Keterangan,s.name Shift, avg(d.volume) Total " \
        #         " from act_delay d left join res_company cp on d.bu_company_id=cp.id left join product_product pp on pp.id=d.product left join product_template pt on pt.id=pp.product_tmpl_id left join master_shift s on d.shift_id=s.id " \
        #         " where d.date_act = '"+date+"'and pt.name in ('RAIN','SLIPPERY') and cp.id='"+bu_id+"' group by pt.name,s.name,d.date_act order by date_act,shift)rsdetail group by date)rs on ob.item=rs.item " \
        #         " left join(select 'Value' item,sum(ab.volume) act " \
        #         " from act_barging ab left join master_sub_activity sa on sa.id = ab.sub_activity_id left join res_company cp on ab.bu_company_id = cp.id " \
        #         "where ab.date_act = '"+date+"' and ab.active=TRUE and ab.state='complete' and cp.id='"+bu_id+"')barg on ob.item=barg.item)dataaktual on dataplan.item=dataaktual.item"
        # return query

    def QueryCGMTD(self, date, bu_id):
        # date = date.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "DO $$ DECLARE tgl date; " \
                "iup integer[]; " \
                "BEGIN  " \
                "SELECT  " \
                " '"+date+"' INTO tgl; " \
                "SELECT  " \
                "  ARRAY['"+str(bu_id)+"'] INTO iup; " \
                "DROP  " \
                "  TABLE IF EXISTS plan_mtd_cg; " \
                "DROP  " \
                "  TABLE IF EXISTS aktual_mtd_cg; " \
                "DROP  " \
                "  TABLE IF EXISTS plan_eom_cg; " \
                "DROP  " \
                "  TABLE IF EXISTS plan_mtd_ob; " \
                "DROP  " \
                "  TABLE IF EXISTS aktual_mtd_ob; " \
                "create table aktual_mtd_cg as  " \
                "select  " \
                "  'AKTUAL MTD' item,  " \
                "  sum(ap.volume) volume  " \
                "from  " \
                "  act_production ap  " \
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "  left join res_company cp on ap.bu_company_id = cp.id  " \
                "where  " \
                "  ap.date_act between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and ap.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'COAL GETTING'  " \
                "  and cp.id = any(iup); " \
                "create table plan_mtd_cg as  " \
                "select  " \
                "  'PLAN MTD' item,  " \
                "  sum(pp.volume_plan) volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'COAL GETTING'  " \
                "  and cp.id = any(iup); " \
                "create table plan_eom_cg as  " \
                "select  " \
                "  'PLAN EOM' item,  " \
                "  sum(pp.volume_plan) volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and date( " \
                "    date_trunc('month', tgl) + interval '1 month' - interval '1 day' " \
                "  )  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'COAL GETTING'  " \
                "  and cp.id = any(iup); " \
                "create table plan_mtd_ob as  " \
                "select  " \
                "  'PLAN MTD' item,  " \
                "  sum(pp.volume_plan) volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'OVERBURDEN'  " \
                "  and cp.id = any(iup); " \
                "create table aktual_mtd_ob as  " \
                "select  " \
                "  'AKTUAL MTD' item,  " \
                "  sum(ap.volume) volume  " \
                "from  " \
                "  act_production ap  " \
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "  left join res_company cp on ap.bu_company_id = cp.id  " \
                "where  " \
                "  ap.date_act between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and ap.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'OVERBURDEN'  " \
                "  and cp.id = any(iup); " \
                "end$$; " \
                "select  " \
                "  *  " \
                "from  " \
                "  plan_mtd_cg  " \
                "UNION ALL  " \
                "SELECT  " \
                "  *  " \
                "FROM  " \
                "  PLAN_EOM_CG  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN SR' COAL_GETTING,  " \
                "  ob.volume / coal.volume plan  " \
                "from  " \
                "  plan_mtd_cg coal  " \
                "  left join plan_mtd_ob ob on coal.item = ob.item  " \
                "UNION ALL  " \
                "SELECT  " \
                "  *  " \
                "FROM  " \
                "  AKTUAL_MTD_CG  " \
                "UNION ALL  " \
                "select  " \
                "  'AKTUAL SR' COAL_GETTING,  " \
                "  ob.volume / coal.volume actual  " \
                "from  " \
                "  aktual_mtd_cg coal  " \
                "  left join aktual_mtd_ob ob on coal.item = ob.item "
        # query = "select 'AKTUAL MTD' Item,sum(ap.volume) act from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date(date_trunc('month', date('"+date+"'))) and '"+date+"'" \
        #         "and ap.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"'" \
        #         " UNION ALL " \
        #         " select 'PLAN MTD' item,sum(pp.volume_plan) act from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('month', date('"+date+"'))) and '"+date+"'" \
        #         " and pp.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"'" \
        #         " UNION ALL" \
        #         " select 'PLAN EOM' item,sum(pp.volume_plan) act from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('month', date('"+date+"'))) and date(date_trunc('month', date('"+date+"')) + interval '1 month' - interval '1 day') " \
        #         " and pp.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"'" \
        #         " UNION ALL" \
        #         " select coal.item, ob.volume/coal.volume plan " \
        #         " from(select 'SR Plan' item,sum(pp.volume_plan) volume from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('month', date('"+date+"'))) and '"+date+"' " \
        #         " and pp.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"') coal left join(select 'SR Plan' item,sum(pp.volume_plan) volume from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('month', date('"+date+"'))) and '"+date+"'" \
        #         " and pp.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"')ob on coal.item=ob.item" \
        #         " UNION ALL" \
        #         " select coal.item, ob.volume/coal.volume actual from(select 'SR Actual' item,sum(ap.volume) volume from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date(date_trunc('month', date('"+date+"'))) and '"+date+"'" \
        #         " and ap.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"') coal left join(" \
        #         " select 'SR Actual' item,sum(ap.volume) volume from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date(date_trunc('month', date('"+date+"'))) and '"+date+"'" \
        #         " and ap.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"')ob on coal.item=ob.item"
        return query

    def QueryCGYTD(self, date, bu_id):
        # date = date.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = " DO $$ DECLARE tgl date;  " \
                " iup integer[]; " \
                " BEGIN  " \
                " SELECT  " \
                "   '"+date+"' INTO tgl; " \
                " SELECT  " \
                "   ARRAY['"+str(bu_id)+"'] INTO iup; " \
                " DROP  " \
                "   TABLE IF EXISTS plan_YTD_cg; " \
                " DROP  " \
                "   TABLE IF EXISTS aktual_YTD_cg; " \
                " DROP  " \
                "   TABLE IF EXISTS plan_eom_cg; " \
                " DROP  " \
                "   TABLE IF EXISTS plan_YTD_ob; " \
                " DROP  " \
                "   TABLE IF EXISTS aktual_YTD_ob; " \
                " create table aktual_YTD_cg as  " \
                " select  " \
                "   'AKTUAL YTD' item,  " \
                "   sum(ap.volume) volume  " \
                " from  " \
                "   act_production ap  " \
                "   left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "   left join res_company cp on ap.bu_company_id = cp.id  " \
                " where  " \
                "   ap.date_act between date( " \
                "     date_trunc('year', tgl) " \
                "   )  " \
                "   and tgl  " \
                "   and ap.active = TRUE  " \
                "   and state = 'complete'  " \
                "   and sa.name = 'COAL GETTING'  " \
                "   and cp.id = any(iup); " \
                " create table plan_YTD_cg as  " \
                " select  " \
                "   'PLAN YTD' item,  " \
                "   sum(pp.volume_plan) volume  " \
                " from  " \
                "   planning_production pp  " \
                "   left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "   left join res_company cp on pp.bu_company_id = cp.id  " \
                " where  " \
                "   pp.date_START between date( " \
                "     date_trunc('year', tgl) " \
                "   )  " \
                "   and tgl  " \
                "   and pp.active = TRUE  " \
                "   and state = 'complete'  " \
                "   and sa.name = 'COAL GETTING'  " \
                "   and cp.id = any(iup); " \
                " create table plan_eom_cg as  " \
                " select  " \
                "   'PLAN EOY' item,  " \
                "   sum(pp.volume_plan) volume  " \
                " from  " \
                "   planning_production pp  " \
                "   left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "   left join res_company cp on pp.bu_company_id = cp.id  " \
                " where  " \
                "   pp.date_START between date( " \
                "     date_trunc('year', tgl) " \
                "   )  " \
                "   and date( " \
                "     date_trunc('year', tgl) + interval '1 year' - interval '1 day' " \
                "   )  " \
                "   and pp.active = TRUE  " \
                "   and state = 'complete'  " \
                "   and sa.name = 'COAL GETTING'  " \
                "   and cp.id = any(iup); " \
                " create table plan_YTD_ob as  " \
                " select  " \
                "   'PLAN YTD' item,  " \
                "   sum(pp.volume_plan) volume  " \
                " from  " \
                "   planning_production pp  " \
                "   left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "   left join res_company cp on pp.bu_company_id = cp.id  " \
                " where  " \
                "   pp.date_START between date( " \
                "     date_trunc('year', tgl) " \
                "   )  " \
                "   and tgl  " \
                "   and pp.active = TRUE  " \
                "   and state = 'complete'  " \
                "   and sa.name = 'OVERBURDEN'  " \
                "   and cp.id = any(iup); " \
                " create table aktual_YTD_ob as  " \
                " select  " \
                "   'AKTUAL YTD' item,  " \
                "   sum(ap.volume) volume  " \
                " from  " \
                "   act_production ap  " \
                "   left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "   left join res_company cp on ap.bu_company_id = cp.id  " \
                " where  " \
                "   ap.date_act between date( " \
                "     date_trunc('year', tgl) " \
                "   )  " \
                "   and tgl  " \
                "   and ap.active = TRUE  " \
                "   and state = 'complete'  " \
                "   and sa.name = 'OVERBURDEN'  " \
                "   and cp.id = any(iup); " \
                " end$$; " \
                " select  " \
                "   *  " \
                " from  " \
                "   plan_YTD_cg  " \
                " UNION ALL  " \
                " SELECT  " \
                "   *  " \
                " FROM  " \
                "   PLAN_EOM_CG  " \
                " UNION ALL  " \
                " select  " \
                "   'PLAN SR' COAL_GETTING,  " \
                "   ob.volume / coal.volume plan  " \
                " from  " \
                "   plan_YTD_cg coal  " \
                "   left join plan_YTD_ob ob on coal.item = ob.item  " \
                " UNION ALL  " \
                " SELECT  " \
                "   *  " \
                " FROM  " \
                "   AKTUAL_YTD_CG  " \
                " UNION ALL  " \
                " select  " \
                "   'AKTUAL SR' COAL_GETTING,  " \
                "   ob.volume / coal.volume actual  " \
                " from  " \
                "   aktual_YTD_cg coal  " \
                "   left join aktual_YTD_ob ob on coal.item = ob.item "
        # query = "select 'AKTUAL YTD' COAL_GETTING,sum(ap.volume) act " \
        #         " from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id " \
        #         " where  ap.date_act between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and ap.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"'" \
        #         " UNION ALL" \
        #         " select 'PLAN YTD' COAL_GETTING,sum(pp.volume_plan) act " \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and pp.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"'" \
        #         " UNION ALL " \
        #         " select 'PLAN EOY' COAL_GETTING,sum(pp.volume_plan) act " \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('year', date('"+date+"'))) and date(date_trunc('year', date('"+date+"')) + interval '1 year' - interval '1 day') and pp.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"'" \
        #         " UNION ALL " \
        #         " select coal.item COAL_GETTING, ob.volume/coal.volume plan from(select 'SR Plan' item,sum(pp.volume_plan) volume " \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_START between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and pp.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"') coal left join(select 'SR Plan' item,sum(pp.volume_plan) volume " \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and pp.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"')ob on coal.item=ob.item" \
        #         " UNION ALL " \
        #         " select coal.item COAL_GETTING, ob.volume/coal.volume actual " \
        #         " from(select 'SR Actual' item,sum(ap.volume) volume from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and ap.active=TRUE and state='complete' and sa.name='COAL GETTING' and cp.id='"+bu_id+"') coal " \
        #         " left join(select 'SR Actual' item,sum(ap.volume) volume from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and ap.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"')ob on coal.item=ob.item"
        return query

    def QueryOBMTD(self, date, bu_id):
        # date = date.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "DO $$ DECLARE tgl date;  " \
                "iup integer[]; " \
                "BEGIN  " \
                "SELECT  " \
                "  '"+date+"' INTO tgl; " \
                "SELECT  " \
                "  ARRAY['"+str(bu_id)+"'] INTO iup; " \
                "DROP  " \
                "  TABLE IF EXISTS resume; " \
                "create table resume as  " \
                "select  " \
                "  'AKTUAL MTD' Overburden,  " \
                "  sum(ap.volume) Volume  " \
                "from  " \
                "  act_production ap  " \
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "  left join res_company cp on ap.bu_company_id = cp.id  " \
                "where  " \
                "  ap.date_act between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and ap.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'OVERBURDEN'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN MTD' Overburden,  " \
                "  sum(pp.volume_plan) Volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'OVERBURDEN'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN EOM' Overburden,  " \
                "  sum(pp.volume_plan) Volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and date( " \
                "    date_trunc('month', tgl) + interval '1 month' - interval '1 day' " \
                "  )  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'OVERBURDEN'  " \
                "  and cp.id = any(iup); " \
                "end$$; " \
                "select  " \
                "  *  " \
                "from  " \
                "  resume "
        # query = "select 'AKTUAL MTD' Overburden,sum(ap.volume) Volume from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id " \
        #         " where  ap.date_act between date(date_trunc('month', date('"+date+"'))) and '"+date+"' and ap.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"' " \
        #         " UNION ALL " \
        #         " select 'PLAN MTD' Overburden,sum(pp.volume_plan) Volume from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_START between date(date_trunc('month', date('"+date+"'))) and '"+date+"' and pp.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"'" \
        #         " UNION ALL " \
        #         " select 'PLAN EOM' Overburden,sum(pp.volume_plan) Volume from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('month', date('"+date+"'))) and date(date_trunc('month', date('"+date+"')) + interval '1 month' - interval '1 day') and pp.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"'"
        return query

    def QueryOBYTD(self, date, bu_id):
        # date = date.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "DO $$ DECLARE tgl date;  " \
                "iup integer[]; " \
                "BEGIN  " \
                "SELECT  " \
                "  '"+date+"' INTO tgl; " \
                "SELECT  " \
                "  ARRAY['"+str(bu_id)+"'] INTO iup; " \
                "DROP  " \
                "  TABLE IF EXISTS resume; " \
                "create table resume as  " \
                "select  " \
                "  'AKTUAL YTD' Overburden,  " \
                "  sum(ap.volume) Volume  " \
                "from  " \
                "  act_production ap  " \
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "  left join res_company cp on ap.bu_company_id = cp.id  " \
                "where  " \
                "  ap.date_act between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and ap.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'OVERBURDEN'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN YTD' Overburden,  " \
                "  sum(pp.volume_plan) Volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'OVERBURDEN'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN EOY' Overburden,  " \
                "  sum(pp.volume_plan) Volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and date( " \
                "    date_trunc('year', tgl) + interval '1 year' - interval '1 day' " \
                "  )  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'OVERBURDEN'  " \
                "  and cp.id = any(iup); " \
                "end$$; " \
                "select  " \
                "  *  " \
                "from  " \
                "  resume"
        # query = "select 'AKTUAL YTD' Overburden,sum(ap.volume) Volume from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id " \
        #         " where  ap.date_act between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and ap.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"' " \
        #         " UNION ALL" \
        #         " select 'PLAN YTD' Overburden,sum(pp.volume_plan) Volume from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and pp.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"'" \
        #         " UNION ALL" \
        #         " select 'PLAN EOY' Overburden,sum(pp.volume_plan) Volume from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_START between date(date_trunc('year', date('"+date+"'))) and date(date_trunc('year', date('"+date+"')) + interval '1 year' - interval '1 day') and pp.active=TRUE and state='complete' and sa.name='OVERBURDEN' and cp.id='"+bu_id+"'"
        return query

    def QueryHaulingMTD(self, date, bu_id):
        # date = date.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "DO $$ DECLARE tgl date; " \
                "iup integer[]; " \
                "BEGIN  " \
                "SELECT  " \
                "  '"+date+"' INTO tgl; " \
                "SELECT  " \
                "  ARRAY['"+bu_id+"'] INTO iup; " \
                "DROP  " \
                "  TABLE IF EXISTS resume; " \
                "create table resume as  " \
                "select  " \
                "  'AKTUAL MTD' COAL_HAULING,  " \
                "  sum(ap.volume) Volume  " \
                "from  " \
                "  act_hauling ap  " \
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "  left join res_company cp on ap.bu_company_id = cp.id  " \
                "where  " \
                "  ap.date_act between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and ap.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN MTD' COAL_HAULING,  " \
                "  sum(pp.volume_plan) Volume  " \
                "from  " \
                "  planning_hauling pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN EOM' COAL_HAULING,  " \
                "  sum(pp.volume_plan) Volume  " \
                "from  " \
                "  planning_hauling pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('month', tgl) " \
                "  )  " \
                "  and date( " \
                "    date_trunc('month', tgl) + interval '1 month' - interval '1 day' " \
                "  )  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and cp.id = any(iup); " \
                "end$$; " \
                "select  " \
                "  *  " \
                "from  " \
                "  resume "
        # query = "select 'AKTUAL MTD' COAL_HAULING,sum(ap.volume) Volume " \
        #         " from act_hauling ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date(date_trunc('month', date('"+date+"'))) and '"+date+"' and ap.active=TRUE and state='complete' and cp.id='"+bu_id+"' " \
        #         " UNION ALL " \
        #         " select 'PLAN MTD' COAL_HAULING,sum(pp.volume_plan) Volume " \
        #         " from planning_hauling pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_START between date(date_trunc('month', date('"+date+"'))) and '"+date+"' and pp.active=TRUE and state='complete' and cp.id='"+bu_id+"'" \
        #         " UNION ALL " \
        #         " select 'PLAN EOM' COAL_HAULING,sum(pp.volume_plan) Volume" \
        #         " from planning_hauling pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('month', date('"+date+"'))) and date(date_trunc('month', date('"+date+"')) + interval '1 month' - interval '1 day') and pp.active=TRUE and state='complete' and cp.id='"+bu_id+"'"
        return query

    def QueryHaulingYTD(self, date, bu_id):
        # date = date.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "DO $$ DECLARE tgl date; " \
                "iup integer[]; " \
                "BEGIN  " \
                "SELECT  " \
                "  '"+date+"' INTO tgl; " \
                "SELECT  " \
                "  ARRAY['"+str(bu_id)+"'] INTO iup; " \
                "DROP  " \
                "  TABLE IF EXISTS resume; " \
                "create table resume as  " \
                "select  " \
                "  'AKTUAL YTD' COAL_HAULING,  " \
                "  sum(ap.volume) Volume  " \
                "from  " \
                "  act_hauling ap  " \
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "  left join res_company cp on ap.bu_company_id = cp.id  " \
                "where  " \
                "  ap.date_act between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and ap.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN YTD' COAL_HAULING,  " \
                "  sum(pp.volume_plan) Volume  " \
                "from  " \
                "  planning_hauling pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN EOY' COAL_HAULING,  " \
                "  sum(pp.volume_plan) Volume  " \
                "from  " \
                "  planning_hauling pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and date( " \
                "    date_trunc('year', tgl + interval '1 year')- interval '1 day' " \
                "  )  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and cp.id = any(iup); " \
                "end$$; " \
                "select  " \
                "  *  " \
                "from  " \
                "  resume "
        # query = "select 'AKTUAL YTD' COAL_HAULING,sum(ap.volume) Volume" \
        #         " from act_hauling ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and ap.active=TRUE and state='complete' and cp.id='"+bu_id+"' " \
        #         " UNION ALL " \
        #         " select 'PLAN YTD' COAL_HAULING,sum(pp.volume_plan) Volume" \
        #         " from planning_hauling pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id" \
        #         " where pp.date_START between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and pp.active=TRUE and state='complete' and cp.id='"+bu_id+"'" \
        #         " UNION ALL " \
        #         " select 'PLAN EOY' COAL_HAULING,sum(pp.volume_plan) Volume" \
        #         " from planning_hauling pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on pp.bu_company_id = cp.id " \
        #         " where pp.date_START between date(date_trunc('year', date('"+date+"'))) and date(date_trunc('year', date('"+date+"') + interval '1 year' )- interval '1 day') and pp.active=TRUE and state='complete' and cp.id='"+bu_id+"'"
        return query

    def QueryBargingMTD(self, date, bu_id):
        # date = date.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "DO $$ DECLARE tgl date;" \
                "iup integer[];" \
                "BEGIN " \
                "SELECT " \
                "  '"+date+"' INTO tgl;" \
                "SELECT " \
                "  ARRAY['"+str(bu_id)+"'] INTO iup;" \
                "DROP " \
                "  TABLE IF EXISTS resume;" \
                "create table resume as " \
                "select " \
                "  'PLAN MTD' COAL_BARGING, " \
                "  sum(pb.volume_plan) act " \
                "from " \
                "  planning_barging pb " \
                "  left join master_sub_activity sa on sa.id = pb.sub_activity_id " \
                "  left join res_company cp on pb.bu_company_id = cp.id " \
                "where " \
                "  pb.date_start between date(" \
                "    date_trunc('month', tgl)" \
                "  ) " \
                "  and tgl " \
                "  and pb.active = TRUE " \
                "  and pb.state = 'complete' " \
                "  and cp.id = any(iup) " \
                "UNION ALL " \
                "select " \
                "  'ACTUAL MTD' COAL_BARGING, " \
                "  sum(ab.volume) act " \
                "from " \
                "  act_barging ab " \
                "  left join master_sub_activity sa on sa.id = ab.sub_activity_id " \
                "  left join res_company cp on ab.bu_company_id = cp.id " \
                "where " \
                "  ab.date_act between date(" \
                "    date_trunc('month', tgl)" \
                "  ) " \
                "  and tgl " \
                "  and ab.active = TRUE " \
                "  and ab.state = 'complete' " \
                "  and cp.id = any(iup) " \
                "UNION ALL " \
                "select " \
                "  'PLAN EOM' COAL_BARGING, " \
                "  sum(pb.volume_plan) act " \
                "from " \
                "  planning_barging pb " \
                "  left join master_sub_activity sa on sa.id = pb.sub_activity_id " \
                "  left join res_company cp on pb.bu_company_id = cp.id " \
                "where " \
                "  pb.date_start between date(" \
                "    date_trunc('month', tgl)" \
                "  ) " \
                "  and date(" \
                "    date_trunc('month', tgl) + interval '1 month' - interval '1 day'" \
                "  ) " \
                "  and pb.active = TRUE " \
                "  and pb.state = 'complete' " \
                "  and cp.id = any(iup);" \
                "end$$;" \
                "select " \
                "  * " \
                "from " \
                "  resume"
        # query = "select 'PLAN MTD' COAL_BARGING,sum(pb.volume_plan) act" \
        #         " from planning_barging pb left join master_sub_activity sa on sa.id = pb.sub_activity_id left join res_company cp on pb.bu_company_id = cp.id " \
        #         " where pb.date_start  between date(date_trunc('month', date('"+date+"'))) and '"+date+"' and pb.active=TRUE and pb.state='complete' and cp.id='"+bu_id+"' " \
        #         " UNION ALL " \
        #         " select 'ACTUAL MTD' COAL_BARGING, sum(ab.volume) act" \
        #         " from act_barging ab left join master_sub_activity sa on sa.id = ab.sub_activity_id left join res_company cp on ab.bu_company_id = cp.id" \
        #         " where ab.date_act  between date(date_trunc('month', date('"+date+"'))) and '"+date+"' and ab.active=TRUE and ab.state='complete' and cp.id='"+bu_id+"' " \
        #         " UNION ALL" \
        #         " select 'PLAN EOM' COAL_BARGING,sum(pb.volume_plan) act" \
        #         " from planning_barging pb left join master_sub_activity sa on sa.id = pb.sub_activity_id left join res_company cp on pb.bu_company_id = cp.id" \
        #         " where pb.date_start  between date(date_trunc('month', date('"+date+"'))) and date(date_trunc('month', date('"+date+"')) + interval '1 month' - interval '1 day') and pb.active=TRUE and pb.state='complete' and cp.id='"+bu_id+"'"
        return query

    def QueryBargingYTD(self, date, bu_id):
        # date = date.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "DO $$ DECLARE tgl date;  " \
                "iup integer[]; " \
                "BEGIN  " \
                "SELECT  " \
                "  '"+date+"' INTO tgl; " \
                "SELECT  " \
                "  ARRAY['"+str(bu_id)+"'] INTO iup; " \
                "DROP  " \
                "  TABLE IF EXISTS resume; " \
                "create table resume as  " \
                "select  " \
                "  'PLAN YTD' COAL_BARGING,  " \
                "  sum(pb.volume_plan) act  " \
                "from  " \
                "  planning_barging pb  " \
                "  left join master_sub_activity sa on sa.id = pb.sub_activity_id  " \
                "  left join res_company cp on pb.bu_company_id = cp.id  " \
                "where  " \
                "  pb.date_start between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and pb.active = TRUE  " \
                "  and pb.state = 'complete'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'ACTUAL YTD' COAL_BARGING,  " \
                "  sum(ab.volume) act  " \
                "from  " \
                "  act_barging ab  " \
                "  left join master_sub_activity sa on sa.id = ab.sub_activity_id  " \
                "  left join res_company cp on ab.bu_company_id = cp.id  " \
                "where  " \
                "  ab.date_act between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and tgl  " \
                "  and ab.active = TRUE  " \
                "  and ab.state = 'complete'  " \
                "  and cp.id = any(iup)  " \
                "UNION ALL  " \
                "select  " \
                "  'PLAN EOY' COAL_BARGING,  " \
                "  sum(pb.volume_plan) act  " \
                "from  " \
                "  planning_barging pb  " \
                "  left join master_sub_activity sa on sa.id = pb.sub_activity_id  " \
                "  left join res_company cp on pb.bu_company_id = cp.id  " \
                "where  " \
                "  pb.date_start between date( " \
                "    date_trunc('year', tgl) " \
                "  )  " \
                "  and date( " \
                "    date_trunc('year', tgl + interval '1 year')- interval '1 day' " \
                "  )  " \
                "  and pb.active = TRUE  " \
                "  and pb.state = 'complete'  " \
                "  and cp.id = any(iup); " \
                "end$$; " \
                "select  " \
                "  *  " \
                "from  " \
                "  resume "
        # query = "select 'PLAN YTD' COAL_BARGING,sum(pb.volume_plan) act" \
        #         " from planning_barging pb left join master_sub_activity sa on sa.id = pb.sub_activity_id left join res_company cp on pb.bu_company_id = cp.id" \
        #         " where pb.date_start  between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and pb.active=TRUE and pb.state='complete' and cp.id='"+bu_id+"'" \
        #         " UNION ALL " \
        #         " select 'ACTUAL YTD' COAL_BARGING,sum(ab.volume) act" \
        #         " from act_barging ab left join master_sub_activity sa on sa.id = ab.sub_activity_id left join res_company cp on ab.bu_company_id = cp.id " \
        #         " where ab.date_act  between date(date_trunc('year', date('"+date+"'))) and '"+date+"' and ab.active=TRUE and ab.state='complete' and cp.id='"+bu_id+"'" \
        #         " UNION ALL " \
        #         " select 'PLAN EOY' COAL_BARGING,sum(pb.volume_plan) act from planning_barging pb left join master_sub_activity sa on sa.id = pb.sub_activity_id left join res_company cp on pb.bu_company_id = cp.id " \
        #         " where pb.date_start  between date(date_trunc('year', date('"+date+"'))) and date(date_trunc('year', date('"+date+"') + interval '1 year' )- interval '1 day') and pb.active=TRUE and pb.state='complete' and cp.id='"+bu_id+"'"
        return query

class BcrQeuryInventoryUpdate(Exception):

    def QueryIUSubActivity(self, bu_id):
        bu_id = "','".join([str(elem) for elem in bu_id])
        # print(bu_id) old
        # query = "select inv.sub_activity,max(inv.date) Last_Updated,sum(volume) volume" \
        #         " from view_inventory inv right join (SELECT distinct bisnis_unit,max(date) tgl" \
        #         " FROM view_inventory " \
        #         " group by bisnis_unit) validasi on validasi.bisnis_unit=inv.bisnis_unit and validasi.tgl=inv.date " \
        #         " where inv.bu_id in ('"+bu_id+"') " \
        #         " and inv.date >= '2022-12-31'" \
        #         " group by inv.sub_activity" \
        #         " order by inv.sub_activity desc"
        query = "select inv.sub_activity, " \
                " max(inv.date) Last_Updated, " \
                " sum(volume) volume " \
                " from view_inventory inv " \
                " right join (SELECT distinct bisnis_unit, sub_activity,max(date) tgl " \
                " FROM view_inventory group by bisnis_unit,sub_activity) validasi on validasi.bisnis_unit=inv.bisnis_unit " \
                " and validasi.sub_activity=inv.sub_activity  and  validasi.tgl=inv.date " \
                " left join res_company cp on cp.name=inv.bisnis_unit " \
                " WHERE cp.id in('" + bu_id + "') " \
                                              " and inv.date >'2022-12-31' " \
                                              " group by inv.sub_activity " \
                                              " order by inv.sub_activity desc"
        return query

    def QueryIUIUP(self, bu_id):
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "select bu.code iup,inv.sub_activity,max(inv.date) last_updated,sum(volume) volume" \
                " from view_inventory inv " \
                " right join (SELECT distinct bisnis_unit, sub_activity,max(date) tgl" \
                " FROM view_inventory group by bisnis_unit,sub_activity) validasi on validasi.bisnis_unit=inv.bisnis_unit and validasi.tgl=inv.date and validasi.sub_activity=inv.sub_activity" \
                " left join master_bisnis_unit bu on bu.active=true and inv.bisnis_unit=bu.name " \
                " left join res_company cp on cp.name=inv.bisnis_unit" \
                " where cp.id in ('"+bu_id+"') and inv.date >= '2022-12-31' " \
                " group by bu.code,inv.sub_activity order by bu.code,inv.sub_activity desc"
        return query

    def QueryIUSeam(self, bu_id, sub_activity):
        bu_id = "','".join([str(elem) for elem in bu_id])
        sub_activity = "','".join([str(elem) for elem in sub_activity])
        query = " select inv.sub_activity inventory,bu.code iup,inv.pit,inv.seam," \
                " sum(volume) volume" \
                " from view_inventory inv " \
                " right join (SELECT distinct bisnis_unit, sub_activity,max(date) tgl" \
                " FROM view_inventory" \
                " group by bisnis_unit,sub_activity) validasi on validasi.bisnis_unit=inv.bisnis_unit and validasi.tgl=inv.date " \
                " and validasi.sub_activity=inv.sub_activity" \
                " left join master_bisnis_unit bu on bu.active=true and inv.bisnis_unit=bu.name" \
                " left join res_company cp on cp.name=inv.bisnis_unit " \
                " left join master_sub_activity msa on msa.name=inv.sub_activity" \
                " where cp.id in ('"+bu_id+"') and msa.id in ('"+sub_activity+"') and inv.date >= '2022-12-31' group by bu.code,inv.sub_activity,inv.pit,inv.seam order by inv.sub_activity desc,bu.code,inv.pit,inv.seam"
        return query

class BcrQeuryRangkingBU(Exception):

    def QueryRBUTable(self, date_start, date_end):
        # date_start = date_start.replace("-", "")
        # date_end = date_end.replace("-", "")
        query = "DO $$ DECLARE " \
                "startdate date; " \
                "stopdate date; " \
                "BEGIN  " \
                "SELECT  " \
                "  '"+date_start+"' INTO startdate; " \
                "SELECT  " \
                "  '"+date_end+"' INTO stopdate; " \
                "DROP  " \
                "  TABLE IF EXISTS prod_akt; " \
                "DROP  " \
                "  TABLE IF EXISTS prod_plan; " \
                "DROP  " \
                "  TABLE IF EXISTS hauling_akt; " \
                "DROP  " \
                "  TABLE IF EXISTS hauling_plan; " \
                "DROP " \
                "  TABLE IF EXISTS barging_akt; " \
                "DROP  " \
                "  TABLE IF EXISTS barging_plan; " \
                "CREATE TABLE prod_akt AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'AKTUAL' Item,  " \
                "  sa.name Sub_Activity,  " \
                "  sum(ap.volume) volume  " \
                "from  " \
                "  act_production ap  " \
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "  left join res_company cp on ap.bu_company_id = cp.id  " \
                "where  " \
                "  ap.date_act between startdate  " \
                "  and stopdate  " \
                "  and ap.active = TRUE  " \
                "  and state = 'complete'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE prod_plan AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'PLAN' Sub_Activity,  " \
                "  sa.name,  " \
                "  sum(pp.volume_plan) volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between startdate  " \
                "  and stopdate  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE hauling_akt AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'AKTUAL' Item,  " \
                "  case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' else sa.name end Sub_Activity,  " \
                "  sum(ah.volume) volume  " \
                "from  " \
                "  act_hauling ah  " \
                "  left join master_sub_activity sa on sa.id = ah.sub_activity_id  " \
                "  left join res_company cp on ah.bu_company_id = cp.id  " \
                "where  " \
                "  ah.date_act between startdate  " \
                "  and stopdate  " \
                "  and ah.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'HAULING ROM TO PORT'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE hauling_plan AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'PLAN' item,  " \
                "  case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' else sa.name end Sub_Activity,  " \
                "  sum(ph.volume_plan) volume  " \
                "from  " \
                "  planning_hauling ph  " \
                "  left join master_sub_activity sa on sa.id = ph.sub_activity_id  " \
                "  left join res_company cp on ph.bu_company_id = cp.id  " \
                "where  " \
                "  ph.date_START between startdate  " \
                "  and stopdate  " \
                "  and ph.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'HAULING ROM TO PORT'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE barging_akt AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'AKTUAL' Item,  " \
                "  sa.name Sub_Activity,  " \
                "  sum(ab.volume) volume  " \
                "from  " \
                "  act_barging ab  " \
                "  left join master_sub_activity sa on sa.id = ab.sub_activity_id  " \
                "  left join res_company cp on ab.bu_company_id = cp.id  " \
                "where  " \
                "  ab.date_act between startdate  " \
                "  and stopdate  " \
                "  and ab.active = TRUE  " \
                "  and state = 'complete'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE barging_plan AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'PLAN' item,  " \
                "  sa.name Sub_Activity,  " \
                "  sum(pb.volume_plan) volume  " \
                "from  " \
                "  planning_barging pb  " \
                "  left join master_sub_activity sa on sa.id = pb.sub_activity_id  " \
                "  left join res_company cp on pb.bu_company_id = cp.id  " \
                "where  " \
                "  pb.date_START between startdate  " \
                "  and stopdate  " \
                "  and pb.active = TRUE  " \
                "  and state = 'complete'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "END $$; " \
                "SELECT  " \
                "  bu.code IUP,  " \
                "  max( " \
                "    case when sub_activity = 'OVERBURDEN'  " \
                "    and item = 'AKTUAL' then volume END " \
                "  )/ max( " \
                "    case when sub_activity = 'OVERBURDEN'  " \
                "    and item = 'PLAN' then volume END " \
                "  ) OVERBURDEN,  " \
                "  max( " \
                "    case when sub_activity = 'COAL GETTING'  " \
                "    and item = 'AKTUAL' then volume END " \
                "  )/ max( " \
                "    case when sub_activity = 'COAL GETTING'  " \
                "    and item = 'PLAN' then volume END " \
                "  ) COAL_GETTING,  " \
                "  max( " \
                "    case when sub_activity = 'COAL HAULING'  " \
                "    and item = 'AKTUAL' then volume END " \
                "  )/ max( " \
                "    case when sub_activity = 'COAL HAULING'  " \
                "    and item = 'PLAN' then volume END " \
                "  ) COAL_HAULING,  " \
                "  max( " \
                "    case when sub_activity = 'COAL BARGING'  " \
                "    and item = 'AKTUAL' then volume END " \
                "  )/ max( " \
                "    case when sub_activity = 'COAL BARGING'  " \
                "    and item = 'PLAN' then volume END " \
                "  ) COAL_BARGING  " \
                "FROM  " \
                "  ( " \
                "    SELECT  " \
                "      *  " \
                "    FROM  " \
                "      prod_akt  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      prod_plan  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      hauling_akt  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      hauling_plan  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      barging_akt  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      barging_plan " \
                "  ) DATA  " \
                "  left join master_bisnis_unit bu on bu.active = true  " \
                "  and data.iup = bu.name  " \
                "GROUP BY  " \
                "  bu.code  " \
                "order by  " \
                "  iup "

        return query

    def QueryGIUPPerSubActivity(self, date_start, date_end,sub_activity):
        # date_start = date_start.replace("-", "")
        # date_end = date_end.replace("-", "")
        sub_activity = "','".join([str(elem) for elem in sub_activity])
        query = "DO $$ DECLARE startdate date; " \
                "stopdate date; " \
                "activity integer[]; " \
                "BEGIN  " \
                "SELECT  " \
                "  '"+date_start+"' INTO startdate; " \
                "SELECT  " \
                "  '"+date_end+"' INTO stopdate; " \
                "select  " \
                "  ARRAY['"+str(sub_activity)+"'] into activity; " \
                "DROP  " \
                "  TABLE IF EXISTS prod_akt; " \
                "DROP  " \
                "  TABLE IF EXISTS prod_plan; " \
                "DROP  " \
                "  TABLE IF EXISTS hauling_akt; " \
                "DROP  " \
                "  TABLE IF EXISTS hauling_plan; " \
                "DROP  " \
                "  TABLE IF EXISTS barging_akt; " \
                "DROP  " \
                "  TABLE IF EXISTS barging_plan; " \
                "DROP  " \
                "  TABLE IF EXISTS resume; " \
                "CREATE TABLE prod_akt AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'AKTUAL' Item,  " \
                "  sa.name Sub_Activity,  " \
                "  sum(ap.volume) volume  " \
                "from  " \
                "  act_production ap  " \
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  " \
                "  left join res_company cp on ap.bu_company_id = cp.id  " \
                "where  " \
                "  ap.date_act between startdate  " \
                "  and stopdate  " \
                "  and ap.active = TRUE  " \
                "  and state = 'complete'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE prod_plan AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'PLAN' Sub_Activity,  " \
                "  sa.name,  " \
                "  sum(pp.volume_plan) volume  " \
                "from  " \
                "  planning_production pp  " \
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  " \
                "  left join res_company cp on pp.bu_company_id = cp.id  " \
                "where  " \
                "  pp.date_START between startdate  " \
                "  and stopdate  " \
                "  and pp.active = TRUE  " \
                "  and state = 'complete'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE hauling_akt AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'AKTUAL' Item,  " \
                "  sa.name Sub_Activity,  " \
                "  sum(ah.volume) volume  " \
                "from  " \
                "  act_hauling ah  " \
                "  left join master_sub_activity sa on sa.id = ah.sub_activity_id  " \
                "  left join res_company cp on ah.bu_company_id = cp.id  " \
                "where  " \
                "  ah.date_act between startdate  " \
                "  and stopdate  " \
                "  and ah.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'HAULING ROM TO PORT'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE hauling_plan AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'PLAN' item,  " \
                "  sa.name Sub_Activity,  " \
                "  sum(ph.volume_plan) volume  " \
                "from  " \
                "  planning_hauling ph  " \
                "  left join master_sub_activity sa on sa.id = ph.sub_activity_id  " \
                "  left join res_company cp on ph.bu_company_id = cp.id  " \
                "where  " \
                "  ph.date_START between startdate  " \
                "  and stopdate  " \
                "  and ph.active = TRUE  " \
                "  and state = 'complete'  " \
                "  and sa.name = 'HAULING ROM TO PORT'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE barging_akt AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'AKTUAL' Item,  " \
                "  sa.name Sub_Activity,  " \
                "  sum(ab.volume) volume  " \
                "from  " \
                "  act_barging ab  " \
                "  left join master_sub_activity sa on sa.id = ab.sub_activity_id  " \
                "  left join res_company cp on ab.bu_company_id = cp.id  " \
                "where  " \
                "  ab.date_act between startdate  " \
                "  and stopdate  " \
                "  and ab.active = TRUE  " \
                "  and state = 'complete'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE barging_plan AS  " \
                "select  " \
                "  cp.name IUP,  " \
                "  'PLAN' item,  " \
                "  sa.name Sub_Activity,  " \
                "  sum(pb.volume_plan) volume  " \
                "from  " \
                "  planning_barging pb  " \
                "  left join master_sub_activity sa on sa.id = pb.sub_activity_id  " \
                "  left join res_company cp on pb.bu_company_id = cp.id  " \
                "where  " \
                "  pb.date_START between startdate  " \
                "  and stopdate  " \
                "  and pb.active = TRUE  " \
                "  and state = 'complete'  " \
                "group by  " \
                "  cp.name,  " \
                "  sa.name; " \
                "CREATE TABLE resume AS  " \
                "SELECT  " \
                "  bu.code iup,  " \
                "  sub_activity,  " \
                "  max( " \
                "    case when item = 'PLAN' then volume end " \
                "  ) Plan,  " \
                "  max( " \
                "    case when item = 'AKTUAL' then volume end " \
                "  ) Aktual  " \
                "FROM  " \
                "  ( " \
                "    SELECT  " \
                "      *  " \
                "    FROM  " \
                "      prod_akt  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      prod_plan  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      hauling_akt  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      hauling_plan  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      barging_akt  " \
                "    UNION ALL  " \
                "    select  " \
                "      *  " \
                "    from  " \
                "      barging_plan " \
                "  ) DATA  " \
                "  left join master_bisnis_unit bu on bu.active = true  " \
                "  and data.iup = bu.name  " \
                "  left join master_sub_activity msa on msa.active = true  " \
                "  and msa.name = data.sub_activity  " \
                "where  " \
                "  msa.id = any(activity)  " \
                "group by  " \
                "  bu.code,  " \
                "  sub_activity  " \
                "order by  " \
                "  iup; " \
                "END $$; " \
                "SELECT  " \
                "  iup,  " \
                "  case when sub_activity = 'HAULING ROM TO PORT' then 'COAL HAULING' else sub_activity end activity,  " \
                "  plan,  " \
                "  aktual  " \
                "from  " \
                "  resume "


        return query

class BcrQeuryRangkingKontraktor(Exception):

    def QueryRKTable(self, date_start, date_end, bu_id):
        # date_start = date_start.replace("-", "")
        # date_end = date_end.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = "DO $$ DECLARE startdate date; "\
                "stopdate date; "\
                "iup integer[]; "\
                "BEGIN  "\
                "SELECT  "\
                "  '"+date_start+"' INTO startdate; "\
                "SELECT  "\
                "  '"+date_end+"' INTO stopdate; "\
                "select  "\
                "  ARRAY['"+str(bu_id)+"'] into iup; "\
                "DROP  "\
                "  TABLE IF EXISTS prod_akt; "\
                "DROP  "\
                "  TABLE IF EXISTS prod_plan; "\
                "DROP  "\
                "  TABLE IF EXISTS hauling_akt; "\
                "DROP  "\
                "  TABLE IF EXISTS barging_akt; "\
                "create table prod_akt as  "\
                "select  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ) Kontraktor,  "\
                "  'AKTUAL' Item,  "\
                "  sa.name Sub_Activity,  "\
                "  sum(ap.volume) volume  "\
                "from  "\
                "  act_production ap  "\
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  "\
                "  left join res_company cp on ap.bu_company_id = cp.id  "\
                "  left join res_partner kon on kon.active = true  "\
                "  and kon.id = ap.kontraktor_id  "\
                "where  "\
                "  ap.date_act between startdate  "\
                "  and stopdate  "\
                "  and ap.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and cp.id = any(iup)  "\
                "group by  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ),  "\
                "  sa.name; "\
                "create table prod_plan as  "\
                "select  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ) Kontraktor,  "\
                "  'PLAN' Sub_Activity,  "\
                "  sa.name,  "\
                "  sum(pp.volume_plan) volume  "\
                "from  "\
                "  planning_production pp  "\
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  "\
                "  left join res_company cp on pp.bu_company_id = cp.id  "\
                "  left join res_partner kon on kon.active = true  "\
                "  and kon.id = pp.kontraktor_id  "\
                "where  "\
                "  pp.date_START between startdate  "\
                "  and stopdate  "\
                "  and pp.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and cp.id = any(iup)  "\
                "group by  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ),  "\
                "  sa.name; "\
                "create table hauling_akt as  "\
                "select  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ) Kontraktor,  "\
                "  'AKTUAL' Item,  "\
                "  case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' end Sub_Activity,  "\
                "  sum(ah.volume) volume  "\
                "from  "\
                "  act_hauling ah  "\
                "  left join master_sub_activity sa on sa.id = ah.sub_activity_id  "\
                "  left join res_company cp on cp.active = true  "\
                "  and ah.bu_company_id = cp.id  "\
                "  left join res_partner kon on kon.active = true  "\
                "  and kon.id = ah.kontraktor_id  "\
                "where  "\
                "  ah.date_act between startdate  "\
                "  and stopdate  "\
                "  and ah.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and cp.id = any(iup)  "\
                "  and sa.name = 'HAULING ROM TO PORT'  "\
                "group by  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ),  "\
                "  case when sa.name = 'HAULING ROM TO PORT' then 'COAL HAULING' end; "\
                "create table barging_akt as  "\
                "select  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ) Kontraktor,  "\
                "  'AKTUAL' Item,  "\
                "  sa.name Sub_Activity,  "\
                "  sum(ab.volume) volume  "\
                "from  "\
                "  act_barging ab  "\
                "  left join master_sub_activity sa on sa.id = ab.sub_activity_id  "\
                "  left join res_company cp on cp.active = true  "\
                "  and ab.bu_company_id = cp.id  "\
                "  left join res_partner kon on kon.active = true  "\
                "  and kon.id = ab.kontraktor_id  "\
                "where  "\
                "  ab.date_act between startdate  "\
                "  and stopdate  "\
                "  and ab.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and cp.id = any(iup)  "\
                "group by  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ),  "\
                "  sa.name; "\
                "end$$; "\
                "select  "\
                "  kontraktor,  "\
                "  max( "\
                "    case when sub_activity = 'OVERBURDEN' then ach end "\
                "  ) Overburden,  "\
                "  max( "\
                "    case when sub_activity = 'COAL GETTING' then ach end "\
                "  ) Coal_Getting,  "\
                "  max( "\
                "    case when sub_activity = 'COAL HAULING' then ach end "\
                "  ) Coal_Hauling,  "\
                "  max( "\
                "    case when sub_activity = 'COAL BARGING' then ach end "\
                "  ) Coal_Barging  "\
                "from  "\
                "  ( "\
                "    select  "\
                "      Kontraktor,  "\
                "      sub_activity,  "\
                "      max( "\
                "        case when item = 'PLAN' then volume end "\
                "      ) Plan,  "\
                "      max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) Aktual,  "\
                "      max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) / max( "\
                "        case when item = 'PLAN' then volume end "\
                "      ) Ach  "\
                "    from  "\
                "      ( "\
                "        select  "\
                "          *  "\
                "        from  "\
                "          prod_akt  "\
                "        UNION ALL  "\
                "        select  "\
                "          *  "\
                "        from  "\
                "          prod_plan "\
                "      ) data  "\
                "    group by  "\
                "      Kontraktor,  "\
                "      sub_activity  "\
                "    union all  "\
                "    select  "\
                "      Kontraktor,  "\
                "      sub_activity,  "\
                "      max( "\
                "        case when item = 'PLAN' then volume end "\
                "      ) Plan,  "\
                "      max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) Aktual,  "\
                "      case when max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) / max( "\
                "        case when item = 'PLAN' then volume end "\
                "      ) is null then max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) else max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) / max( "\
                "        case when item = 'PLAN' then volume end "\
                "      ) end Ach  "\
                "    from  "\
                "      ( "\
                "        select  "\
                "          *  "\
                "        from  "\
                "          barging_akt "\
                "      ) data  "\
                "    group by  "\
                "      Kontraktor,  "\
                "      sub_activity "\
                "    union all  "\
                "    select  "\
                "      Kontraktor,  "\
                "      sub_activity,  "\
                "      max( "\
                "        case when item = 'PLAN' then volume end "\
                "      ) Plan,  "\
                "      max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) Aktual,  "\
                "      case when max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) / max( "\
                "        case when item = 'PLAN' then volume end "\
                "      ) is null then max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) else max( "\
                "        case when item = 'AKTUAL' then volume end "\
                "      ) / max( "\
                "        case when item = 'PLAN' then volume end "\
                "      ) end Ach  "\
                "    from  "\
                "      ( "\
                "        select  "\
                "          *  "\
                "        from "\
                "         hauling_akt "\
                "      ) data  "\
                "    group by  "\
                "      Kontraktor,  "\
                "      sub_activity  "\
                "    order by  "\
                "      Kontraktor,  "\
                "      sub_activity "\
                "  ) data2  "\
                "group by  "\
                "  kontraktor  "\
                "order by  "\
                "  coal_getting,  "\
                "  coal_hauling desc "

        return query

    def QueryRKGraphic(self, date_start, date_end, bu_id, sub_activity):
        # date_start = date_start.replace("-", "")
        # date_end = date_end.replace("-", "")
        bu_id = "','".join([str(elem) for elem in bu_id])
        sub_activity = "','".join([str(elem) for elem in sub_activity])
        # print(str(bu_id))
        # bu_id = request.env['res.company'].sudo().search([('id', '=', bu_id)]).name
        query = "DO $$ DECLARE startdate date; "\
                "stopdate date; "\
                "iup integer[]; "\
                "activity integer[]; "\
                "BEGIN  "\
                "SELECT  "\
                "  '"+date_start+"' INTO startdate; "\
                "SELECT  "\
                "  '"+date_end+"' INTO stopdate; "\
                "select  "\
                "  ARRAY['"+str(bu_id)+"'] into iup; "\
                "select  "\
                "  ARRAY['"+str(sub_activity)+"'] into activity; "\
                "DROP  "\
                "  TABLE IF EXISTS prod_akt; "\
                "DROP  "\
                "  TABLE IF EXISTS prod_plan; "\
                "DROP  "\
                "  TABLE IF EXISTS hauling_akt; "\
                "DROP  "\
                "  TABLE IF EXISTS barging_akt; "\
                "DROP  "\
                "  TABLE IF EXISTS resume; "\
                "create table prod_akt as  "\
                "select  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ) Kontraktor,  "\
                "  'AKTUAL' Item,  "\
                "  sa.name Sub_Activity,  "\
                "  sum(ap.volume) volume  "\
                "from  "\
                "  act_production ap  "\
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  "\
                "  left join res_company cp on cp.active = true  "\
                "  and ap.bu_company_id = cp.id  "\
                "  left join res_partner kon on kon.active = true  "\
                "  and kon.id = ap.kontraktor_id  "\
                "where  "\
                "  ap.date_act between startdate  "\
                "  and stopdate  "\
                "  and ap.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and cp.id = any(iup)  "\
                "group by  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ),  "\
                "  sa.name; "\
                "create table prod_plan as  "\
                "select  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ) Kontraktor,  "\
                "  'PLAN' Sub_Activity,  "\
                "  sa.name,  "\
                "  sum(pp.volume_plan) volume  "\
                "from  "\
                "  planning_production pp  "\
                "  left join master_sub_activity sa on sa.id = pp.sub_activity_id  "\
                "  left join res_company cp on cp.active = true  "\
                "  and pp.bu_company_id = cp.id  "\
                "  left join res_partner kon on kon.active = true  "\
                "  and kon.id = pp.kontraktor_id  "\
                "where  "\
                "  pp.date_START between startdate  "\
                "  and stopdate  "\
                "  and pp.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and cp.id = any(iup)  "\
                "group by  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ),  "\
                "  sa.name; "\
                "create table hauling_akt as  "\
                "select  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ) Kontraktor,  "\
                "  'AKTUAL' Item,  "\
                "  sa.name Sub_Activity,  "\
                "  sum(ah.volume) volume  "\
                "from  "\
                "  act_hauling ah  "\
                "  left join master_sub_activity sa on sa.id = ah.sub_activity_id  "\
                "  left join res_company cp on cp.active = true  "\
                "  and ah.bu_company_id = cp.id  "\
                "  left join res_partner kon on kon.active = true  "\
                "  and kon.id = ah.kontraktor_id  "\
                "where  "\
                "  ah.date_act between startdate  "\
                "  and stopdate  "\
                "  and ah.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and cp.id = any(iup)  "\
                "  and sa.name = 'HAULING ROM TO PORT'  "\
                "group by  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ),  "\
                "  sa.name; "\
                "create table barging_akt as  "\
                "select  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ) Kontraktor,  "\
                "  'AKTUAL' Item,  "\
                "  sa.name Sub_Activity,  "\
                "  sum(ab.volume) volume  "\
                "from  "\
                "  act_barging ab  "\
                "  left join master_sub_activity sa on sa.id = ab.sub_activity_id  "\
                "  left join res_company cp on cp.active = true  "\
                "  and ab.bu_company_id = cp.id  "\
                "  left join res_partner kon on kon.active = true  "\
                "  and kon.id = ab.kontraktor_id  "\
                "where  "\
                "  ab.date_act between startdate  "\
                "  and stopdate  "\
                "  and ab.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and cp.id = any(iup)  "\
                "group by  "\
                "  left( "\
                "    kon.name,  "\
                "    position('-' in kon.name)-2 "\
                "  ),  "\
                "  sa.name; "\
                "create table resume as  "\
                "select  "\
                "  kontraktor,  "\
                "  sub_activity,  "\
                "  max( "\
                "    case when item = 'PLAN' then volume end "\
                "  ) Plan,  "\
                "  max( "\
                "    case when item = 'AKTUAL' then volume end "\
                "  ) Aktual  "\
                "from  "\
                "  ( "\
                "    select  "\
                "      kontraktor,  "\
                "      item,  "\
                "      sub_activity,  "\
                "      volume  "\
                "    from  "\
                "      ( "\
                "        select  "\
                "          *  "\
                "        from  "\
                "          prod_akt  "\
                "        UNION ALL  "\
                "        select  "\
                "          *  "\
                "        from  "\
                "          prod_plan  "\
                "        union all  "\
                "        select  "\
                "          *  "\
                "        from  "\
                "          barging_akt  "\
                "        UNION ALL  "\
                "        select  "\
                "          *  "\
                "        from  "\
                "          hauling_akt "\
                "      ) data  "\
                "      left join master_sub_activity msa on msa.active = true  "\
                "      and msa.name = data.sub_activity  "\
                "    where  "\
                "      msa.id = any(activity) "\
                "  ) data2  "\
                "group by  "\
                "  kontraktor,  "\
                "  sub_activity; "\
                "end$$; "\
                "select  "\
                "  kontraktor,  "\
                "  case when sub_activity = 'HAULING ROM TO PORT' then 'COAL HAULING' else sub_activity end sub_activity,  "\
                "  plan,  "\
                "  aktual  "\
                "from  "\
                "  resume "

        # query old
        # query = "select kontraktor, sub_activity, " \
        #         " max(case when item='PLAN' then volume end) Plan, " \
        #         " max(case when item='AKTUAL' then volume end) Aktual" \
        #         " from (select kontraktor,item,sub_activity,volume from (select left(kon.name,position('-' in kon.name)-2) Kontraktor,'AKTUAL' Item,sa.name Sub_Activity,sum(ap.volume) volume" \
        #         " from act_production ap" \
        #         " left join master_sub_activity sa on sa.id = ap.sub_activity_id" \
        #         " left join res_company cp on  cp.active=true and ap.bu_company_id = cp.id" \
        #         " left join res_partner kon on kon.active=true and kon.id=ap.kontraktor_id" \
        #         " where  ap.date_act between date('"+date_start+"') and date('"+date_end+"') and ap.active=TRUE and state='complete'group by left(kon.name,position('-' in kon.name)-2),sa.name" \
        #         " UNION ALL " \
        #         " select left(kon.name,position('-' in kon.name)-2) Kontraktor,'PLAN' Sub_Activity,sa.name,sum(pp.volume_plan) volume" \
        #         " from planning_production pp " \
        #         " left join master_sub_activity sa on sa.id = pp.sub_activity_id " \
        #         " left join res_company cp on cp.active=true and pp.bu_company_id = cp.id " \
        #         " left join res_partner kon on kon.active=true and kon.id=pp.kontraktor_id " \
        #         " where pp.date_START between date('"+date_start+"') and date('"+date_end+"') and pp.active=TRUE and state='complete' group by left(kon.name,position('-' in kon.name)-2),sa.name" \
        #         " union all" \
        #         " select left(kon.name,position('-' in kon.name)-2) Kontraktor,'AKTUAL' Item,sa.name Sub_Activity,sum(ab.volume) volume" \
        #         " from act_barging ab" \
        #         " left join master_sub_activity sa on sa.id = ab.sub_activity_id " \
        #         " left join res_company cp on  cp.active=true and ab.bu_company_id = cp.id " \
        #         " left join res_partner kon on kon.active=true and kon.id=ab.kontraktor_id " \
        #         " where  ab.date_act between date('"+date_start+"') and date('"+date_end+"') and ab.active=TRUE and state='complete' group by left(kon.name,position('-' in kon.name)-2),sa.name" \
        #         " UNION ALL " \
        #         " select left(kon.name,position('-' in kon.name)-2) Kontraktor,'AKTUAL' Item,case when sa.name ='HAULING ROM TO PORT' then 'COAL HAULING' end Sub_Activity,sum(ah.volume) volume" \
        #         " from act_hauling ah " \
        #         " left join master_sub_activity sa on sa.id = ah.sub_activity_id " \
        #         " left join res_company cp on  cp.active=true and ah.bu_company_id = cp.id " \
        #         " left join res_partner kon on kon.active=true and kon.id=ah.kontraktor_id " \
        #         " where  ah.date_act between date('"+date_start+"') and date('"+date_end+"') and ah.active=TRUE and state='complete' group by left(kon.name,position('-' in kon.name)-2),case when sa.name ='HAULING ROM TO PORT' then 'COAL HAULING' end) data" \
        #         " where sub_activity='COAL GETTING')data2 group by kontraktor,sub_activity"
        # query old
        # query = "select kon.name Kontraktor,'AKTUAL' Item,sa.name Sub_Activity,sum(ap.volume) volume" \
        #         " from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on  cp.active=true and ap.bu_company_id = cp.id left join res_partner kon on kon.active=true and kon.id=ap.kontraktor_id" \
        #         " where  ap.date_act between date('"+date_start+"') and date('"+date_end+"') and ap.active=TRUE and state='complete' and cp.id='"+bu_id+"' group by kon.name,sa.name" \
        #         " UNION ALL" \
        #         " select kon.name Kontraktor,'PLAN' Sub_Activity,sa.name,sum(pp.volume_plan) volume" \
        #         " from planning_production pp left join master_sub_activity sa on sa.id = pp.sub_activity_id left join res_company cp on cp.active=true and pp.bu_company_id = cp.id left join res_partner kon on kon.active=true and kon.id=pp.kontraktor_id" \
        #         " where pp.date_START between date('"+date_start+"') and date('"+date_end+"') and pp.active=TRUE and state='complete' and cp.id='"+bu_id+"' group by kon.name,sa.name" \
        #         " union all" \
        #         " select kon.name Kontraktor,'AKTUAL' Item,sa.name Sub_Activity,sum(ab.volume) volume" \
        #         " from act_barging ab left join master_sub_activity sa on sa.id = ab.sub_activity_id left join res_company cp on  cp.active=true and ab.bu_company_id = cp.id left join res_partner kon on kon.active=true and kon.id=ab.kontraktor_id" \
        #         " where  ab.date_act between date('"+date_start+"') and date('"+date_end+"') and ab.active=TRUE and state='complete' and cp.id='"+bu_id+"' group by kon.name,sa.name" \
        #         " UNION ALL " \
        #         " select kon.name Kontraktor,'AKTUAL' Item,case when sa.name ='HAULING ROM TO PORT' then 'COAL HAULING' end Sub_Activity,sum(ah.volume) volume " \
        #         " from act_hauling ah left join master_sub_activity sa on sa.id = ah.sub_activity_id left join res_company cp on  cp.active=true and ah.bu_company_id = cp.id left join res_partner kon on kon.active=true and kon.id=ah.kontraktor_id" \
        #         " where  ah.date_act between date('"+date_start+"') and date('"+date_end+"') and ah.active=TRUE and state='complete' and cp.id='"+bu_id+"' group by kon.name,case when sa.name ='HAULING ROM TO PORT' then 'COAL HAULING' end"
        return query

class BcrQeuryBestAchivement(Exception):

    def QueryPivotTableDaily(self, date_start, date_end, sub_activity):
        # date_start = date_start.replace("-", "")
        # date_end = date_end.replace("-", "")
        sub_activity = "','".join([str(elem) for elem in sub_activity])
        query = "DO $$ DECLARE startdate date; "\
                "stopdate date; "\
                "activity integer[]; "\
                "BEGIN  "\
                "SELECT  "\
                "  '"+date_start+"' INTO startdate; "\
                "SELECT  "\
                "  '"+date_end+"' INTO stopdate; "\
                "SELECT  "\
                "  array['"+str(sub_activity)+"'] INTO activity; "\
                "DROP  "\
                "  TABLE IF EXISTS prod_akt; "\
                "DROP  "\
                "  TABLE IF EXISTS hauling_akt; "\
                "DROP  "\
                "  TABLE IF EXISTS barging_akt; "\
                "DROP  "\
                "  TABLE IF EXISTS resume; "\
                "CREATE TABLE prod_akt AS  "\
                "select  "\
                "  ap.date_act Date,  "\
                "  bu.code IUP,  "\
                "  sa.name Sub_Activity,  "\
                "  sum(ap.volume) volume  "\
                "from  "\
                "  act_production ap  "\
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id  "\
                "  left join res_company cp on ap.bu_company_id = cp.id  "\
                "  left join master_bisnis_unit bu on bu.active = true  "\
                "  and cp.name = bu.name  "\
                "where  "\
                "  ap.date_act between startdate  "\
                "  and stopdate  "\
                "  and ap.active = TRUE  "\
                "  and state = 'complete'  "\
                "group by  "\
                "  bu.code,  "\
                "  sa.name,  "\
                "  ap.date_act  "\
                "order by  "\
                "  date; "\
                "CREATE TABLE hauling_akt AS  "\
                "select  "\
                "  ah.date_act date,  "\
                "  bu.code IUP,  "\
                "  sa.name Sub_activity,  "\
                "  sum(ah.volume) volume  "\
                "from  "\
                "  act_hauling ah  "\
                "  left join master_sub_activity sa on sa.id = ah.sub_activity_id  "\
                "  left join res_company cp on ah.bu_company_id = cp.id  "\
                "  left join master_bisnis_unit bu on bu.active = true  "\
                "  and cp.name = bu.name  "\
                "where  "\
                "  ah.date_act between startdate  "\
                "  and stopdate  "\
                "  and ah.active = TRUE  "\
                "  and state = 'complete'  "\
                "  and sa.name = 'HAULING ROM TO PORT'  "\
                "group by  "\
                "  ah.date_act,  "\
                "  bu.code,  "\
                "  sa.name  "\
                "order by  "\
                "  date; "\
                "CREATE TABLE barging_akt AS  "\
                "select  "\
                "  ab.date_act date,  "\
                "  bu.code IUP,  "\
                "  sa.name Sub_Activity,  "\
                "  sum(ab.volume) volume  "\
                "from  "\
                "  act_barging ab  "\
                "  left join master_sub_activity sa on sa.id = ab.sub_activity_id  "\
                "  left join res_company cp on ab.bu_company_id = cp.id  "\
                "  left join master_bisnis_unit bu on bu.active = true  "\
                "  and cp.name = bu.name  "\
                "where  "\
                "  ab.date_act between startdate  "\
                "  and stopdate  "\
                "  and ab.active = TRUE  "\
                "  and state = 'complete'  "\
                "group by  "\
                "  bu.code,  "\
                "  sa.name,  "\
                "  ab.date_act  "\
                "order by  "\
                "  date; "\
                "CREATE TABLE resume AS  "\
                "select  "\
                "  data.* "\
                "from  "\
                "  ( "\
                "    select  "\
                "      Date,  "\
                "      IUP,  "\
                "      sub_activity,  "\
                "      Volume  "\
                "    from  "\
                "      hauling_akt  "\
                "    where  "\
                "      volume in ( "\
                "        select  "\
                "          max(volume)  "\
                "        from  "\
                "          hauling_akt  "\
                "        group by  "\
                "          iup,  "\
                "          sub_activity "\
                "      )  "\
                "    union all  "\
                "    select  "\
                "      *  "\
                "    from  "\
                "      prod_akt  "\
                "    where  "\
                "      volume in ( "\
                "        select  "\
                "          max(volume) Volume  "\
                "        from  "\
                "          prod_akt  "\
                "        group by  "\
                "          iup,  "\
                "          sub_activity "\
                "      )  "\
                "    union all  "\
                "    select  "\
                "      *  "\
                "    from  "\
                "      barging_akt  "\
                "    where  "\
                "      volume in ( "\
                "        select  "\
                "          max(volume) Volume  "\
                "        from  "\
                "          barging_akt  "\
                "        group by  "\
                "          iup,  "\
                "          sub_activity "\
                "      )  "\
                "    order by  "\
                "      iup "\
                "  ) data  "\
                "  left join master_sub_activity msa on msa.active = true  "\
                "  and msa.name = data.sub_activity  "\
                "where  "\
                "  msa.id = any(activity); "\
                "END $$; "\
                "select  "\
                "  date,  "\
                "  iup,  "\
                "  case when sub_activity = 'HAULING ROM TO PORT' then 'COAL HAULING' else sub_activity end sub_activity,  "\
                "  volume  "\
                "from  "\
                "  resume "
        return query

    def QueryPivotTableMonthly(self, date_start, date_end, sub_activity):
        # date_start = date_start.replace("-", "")
        # date_end = date_end.replace("-", "")
        sub_activity = "','".join([str(elem) for elem in sub_activity])
        query = "DO $$ DECLARE startdate date;"\
                "stopdate date;"\
                "activity integer[];"\
                "BEGIN "\
                "SELECT "\
                "  '"+date_start+"' INTO startdate;"\
                "SELECT "\
                "  '"+date_end+"' INTO stopdate;"\
                "SELECT "\
                "  array['"+str(sub_activity)+"'] INTO activity;"\
                "DROP "\
                "  TABLE IF EXISTS prod_akt;"\
                "DROP "\
                "  TABLE IF EXISTS hauling_akt;"\
                "DROP "\
                "  TABLE IF EXISTS barging_akt;"\
                "DROP "\
                "  TABLE IF EXISTS resume;"\
                "CREATE TABLE prod_akt AS "\
                "select "\
                "  to_char(ap.date_act, 'Month YYYY') Date, "\
                "  bu.code IUP, "\
                "  sa.name Sub_Activity, "\
                "  sum(ap.volume) volume "\
                "from "\
                "  act_production ap "\
                "  left join master_sub_activity sa on sa.id = ap.sub_activity_id "\
                "  left join res_company cp on ap.bu_company_id = cp.id "\
                "  left join master_bisnis_unit bu on bu.active = true "\
                "  and cp.name = bu.name "\
                "where "\
                "  ap.date_act between startdate "\
                "  and stopdate "\
                "  and ap.active = TRUE "\
                "  and state = 'complete' "\
                "group by "\
                "  bu.code, "\
                "  sa.name, "\
                "  to_char(ap.date_act, 'Month YYYY') "\
                "order by "\
                "  date;"\
                "CREATE TABLE hauling_akt AS "\
                "select "\
                "  to_char(ah.date_act, 'Month YYYY') Date, "\
                "  bu.code IUP, "\
                "  sa.name Sub_Activity, "\
                "  sum(ah.volume) volume "\
                "from "\
                "  act_hauling ah "\
                "  left join master_sub_activity sa on sa.id = ah.sub_activity_id "\
                "  left join res_company cp on ah.bu_company_id = cp.id "\
                "  left join master_bisnis_unit bu on bu.active = true "\
                "  and cp.name = bu.name "\
                "where "\
                "  ah.date_act between startdate "\
                "  and stopdate "\
                "  and ah.active = TRUE "\
                "  and state = 'complete' "\
                "  and sa.name = 'HAULING ROM TO PORT' "\
                "group by "\
                "  bu.code, "\
                "  sa.name, "\
                "  to_char(ah.date_act, 'Month YYYY') "\
                "order by "\
                "  date;"\
                "CREATE TABLE barging_akt AS "\
                "select "\
                "  to_char(ab.date_act, 'Month YYYY') date, "\
                "  bu.code IUP, "\
                "  sa.name Sub_Activity, "\
                "  sum(ab.volume) volume "\
                "from "\
                "  act_barging ab "\
                "  left join master_sub_activity sa on sa.id = ab.sub_activity_id "\
                "  left join res_company cp on ab.bu_company_id = cp.id "\
                "  left join master_bisnis_unit bu on bu.active = true "\
                "  and cp.name = bu.name "\
                "where "\
                "  ab.date_act between startdate "\
                "  and stopdate "\
                "  and ab.active = TRUE "\
                "  and state = 'complete' "\
                "group by "\
                "  bu.code, "\
                "  sa.name, "\
                "  to_char(ab.date_act, 'Month YYYY') "\
                "order by "\
                "  date;"\
                "CREATE TABLE resume AS "\
                "SELECT "\
                "  date, "\
                "  iup, "\
                "  sub_activity, "\
                "  volume "\
                "FROM "\
                "  ("\
                "    select "\
                "      Date, "\
                "      IUP, "\
                "      sub_activity, "\
                "      Volume "\
                "    from "\
                "      hauling_akt "\
                "    where "\
                "      volume in ("\
                "        select "\
                "          max(volume) Volume "\
                "        from "\
                "          hauling_akt "\
                "        group by "\
                "          iup, "\
                "          sub_activity"\
                "      ) "\
                "    union all "\
                "    select "\
                "      * "\
                "    from "\
                "      prod_akt "\
                "    where "\
                "      volume in ("\
                "        select "\
                "          max(volume) Volume "\
                "        from "\
                "          prod_akt "\
                "        group by "\
                "          iup, "\
                "          sub_activity"\
                "      ) "\
                "    union all "\
                "    select "\
                "      * "\
                "    from "\
                "      barging_akt "\
                "    where "\
                "      volume in ("\
                "        select "\
                "          max(volume) Volume "\
                "        from "\
                "          barging_akt "\
                "        group by "\
                "          iup, "\
                "          sub_activity"\
                "      ) "\
                "    order by "\
                "      iup"\
                "  ) DATA "\
                "  left join master_sub_activity msa on msa.active = true "\
                "  and msa.name = data.sub_activity "\
                "where "\
                "  msa.id = any(activity);"\
                "END $$;"\
                "select "\
                "  date, "\
                "  iup, "\
                "  case when sub_activity = 'HAULING ROM TO PORT' then 'COAL HAULING' else sub_activity end sub_activity, "\
                "  volume "\
                "from "\
                "  resume"
        return query

class BcrQeuryProductTrend(Exception):

    def QueryPTMonthlySubActivity(self, date_start, date_end, bu_id, sub_activity):
        # date_start = date_start.replace("-", "")
        # date_end = date_end.replace("-", "")
        # bu_id = request.env['res.company'].sudo().search([('id', '=', bu_id)]).name
        bu_id = ",".join([str(elem) for elem in bu_id])
        query = "DO $$ "\
                "DECLARE startdate date; stopdate date; bisnis_unit integer[]; activity integer; "\
                "BEGIN "\
                "  SELECT '"+date_start+"' INTO startdate; "\
                "	SELECT '"+date_end+"' INTO stopdate; "\
                "	select array["+bu_id+"] into bisnis_unit; "\
                "	select '"+sub_activity+"' into activity; "\
                "	DROP TABLE IF EXISTS prod_akt; "\
                "	DROP TABLE IF EXISTS hauling_akt; "\
                "	DROP TABLE IF EXISTS barging_akt; "\
                "	DROP TABLE IF EXISTS prod_plan; "\
                "	DROP TABLE IF EXISTS hauling_plan; "\
                "	DROP TABLE IF EXISTS barging_plan; "\
                "	DROP TABLE IF EXISTS RAINSLIPPERY; "\
                "	DROP TABLE IF EXISTS RESUME; "\
                "	CREATE TABLE PROD_AKT AS "\
                "	select  "\
                "	to_char(ap.date_act,'YYMM') Date2, "\
                "	to_char(ap.date_act,'Mon YYYY') Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ap.volume) volume "\
                "	from act_production ap "\
                "	left join master_sub_activity sa on sa.id = ap.sub_activity_id "\
                "	left join res_company cp on ap.bu_company_id = cp.id "\
                "	where  ap.date_act between startdate and stopdate "\
                "	and ap.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name,to_char(ap.date_act,'Mon YYYY'),to_char(ap.date_act,'YYMM') "\
                "	union all "\
                "	select  "\
                "	to_char(ap.date_act,'YYMM') Date2, "\
                "	to_char(ap.date_act,'Mon YYYY') Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ap.volume) volume "\
                "	from act_production ap "\
                "	left join master_sub_activity sa on sa.id = ap.sub_activity_id "\
                "	left join res_company cp on ap.bu_company_id = cp.id "\
                "	where  ap.date_act between startdate and stopdate "\
                "	and ap.active=TRUE "\
                "	and state='complete' "\
                "	group by sa.name,to_char(ap.date_act,'Mon YYYY'),to_char(ap.date_act,'YYMM'); "\
                "	CREATE TABLE HAULING_AKT AS "\
                "	select  "\
                "	to_char(ah.date_act,'YYMM') Date2, "\
                "	to_char(ah.date_act,'Mon YYYY') Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ah.volume) volume "\
                "	from act_hauling ah "\
                "	left join master_sub_activity sa on sa.id = ah.sub_activity_id "\
                "	left join res_company cp on ah.bu_company_id = cp.id "\
                "	where  ah.date_act between startdate and stopdate "\
                "	and ah.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name,to_char(ah.date_act,'Mon YYYY'),to_char(ah.date_act,'YYMM') "\
                "	union all "\
                "	select  "\
                "	to_char(ah.date_act,'YYMM') Date2, "\
                "	to_char(ah.date_act,'Mon YYYY') Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ah.volume) volume "\
                "	from act_hauling ah "\
                "	left join master_sub_activity sa on sa.id = ah.sub_activity_id "\
                "	left join res_company cp on ah.bu_company_id = cp.id "\
                "	where  ah.date_act between startdate and stopdate "\
                "	and ah.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by sa.name,to_char(ah.date_act,'Mon YYYY'),to_char(ah.date_act,'YYMM'); "\
                "	CREATE TABLE BARGING_AKT AS "\
                "	select  "\
                "	to_char(ab.date_act,'YYMM') Date2, "\
                "	to_char(ab.date_act,'Mon YYYY') Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ab.volume) volume "\
                "	from act_barging ab "\
                "	left join master_sub_activity sa on sa.id = ab.sub_activity_id "\
                "	left join res_company cp on ab.bu_company_id = cp.id "\
                "	where  ab.date_act between startdate and stopdate "\
                "	and ab.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name,to_char(ab.date_act,'Mon YYYY'),to_char(ab.date_act,'YYMM') "\
                "	union all "\
                "	select  "\
                "	to_char(ab.date_act,'YYMM') Date2, "\
                "	to_char(ab.date_act,'Mon YYYY') Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ab.volume) volume "\
                "	from act_barging ab "\
                "	left join master_sub_activity sa on sa.id = ab.sub_activity_id "\
                "	left join res_company cp on ab.bu_company_id = cp.id "\
                "	where  ab.date_act between startdate and stopdate "\
                "	and ab.active=TRUE "\
                "	and state='complete' "\
                "	group by sa.name,to_char(ab.date_act,'Mon YYYY'),to_char(ab.date_act,'YYMM'); "\
                "	CREATE TABLE PROD_PLAN AS "\
                "	select  "\
                "	to_char(pp.date_start,'YYMM') Date2, "\
                "	to_char(pp.date_start,'Mon YYYY') Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(pp.volume_plan) volume "\
                "	from planning_production pp "\
                "	left join master_sub_activity sa on sa.id = pp.sub_activity_id "\
                "	left join res_company cp on pp.bu_company_id = cp.id "\
                "	where  pp.date_start between startdate and stopdate "\
                "	and pp.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name,to_char(pp.date_start,'Mon YYYY'),to_char(pp.date_start,'YYMM') "\
                "	union all "\
                "	select  "\
                "	to_char(pp.date_start,'YYMM') Date2, "\
                "	to_char(pp.date_start,'Mon YYYY') Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(pp.volume_plan) volume "\
                "	from planning_production pp "\
                "	left join master_sub_activity sa on sa.id = pp.sub_activity_id "\
                "	left join res_company cp on pp.bu_company_id = cp.id "\
                "	where  pp.date_start between startdate and stopdate "\
                "	and pp.active=TRUE "\
                "	and state='complete' "\
                "	group by sa.name,to_char(pp.date_start,'Mon YYYY'),to_char(pp.date_start,'YYMM');	 "\
                "	 "\
                "	CREATE TABLE HAULING_PLAN AS "\
                "	select  "\
                "	to_char(ph.date_start,'YYMM') Date2, "\
                "	to_char(ph.date_start,'Mon YYYY') Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ph.volume_plan) volume "\
                "	from planning_hauling ph "\
                "	left join master_sub_activity sa on sa.id = ph.sub_activity_id "\
                "	left join res_company cp on ph.bu_company_id = cp.id "\
                "	where  ph.date_start between startdate and stopdate "\
                "	and ph.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name,to_char(ph.date_start,'Mon YYYY'),to_char(ph.date_start,'YYMM') "\
                "	union all "\
                "	select  "\
                "	to_char(ph.date_start,'YYMM') Date2, "\
                "	to_char(ph.date_start,'Mon YYYY') Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ph.volume_plan) volume "\
                "	from planning_hauling ph "\
                "	left join master_sub_activity sa on sa.id = ph.sub_activity_id "\
                "	left join res_company cp on ph.bu_company_id = cp.id "\
                "	where  ph.date_start between startdate and stopdate "\
                "	and ph.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by sa.name,to_char(ph.date_start,'Mon YYYY'),to_char(ph.date_start,'YYMM'); "\
                "	 "\
                "	CREATE TABLE BARGING_PLAN AS "\
                "	select  "\
                "	to_char(pb.date_start,'YYMM') Date2, "\
                "	to_char(pb.date_start,'Mon YYYY') Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(pb.volume_plan) volume "\
                "	from planning_barging pb "\
                "	left join master_sub_activity sa on sa.id = pb.sub_activity_id "\
                "	left join res_company cp on pb.bu_company_id = cp.id "\
                "	where  pb.date_start between startdate and stopdate "\
                "	and pb.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name,to_char(pb.date_start,'Mon YYYY'),to_char(pb.date_start,'YYMM') "\
                "	union all "\
                "	select  "\
                "	to_char(pb.date_start,'YYMM') Date2, "\
                "	to_char(pb.date_start,'Mon YYYY') Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(pb.volume_plan) volume "\
                "	from planning_barging pb "\
                "	left join master_sub_activity sa on sa.id = pb.sub_activity_id "\
                "	left join res_company cp on pb.bu_company_id = cp.id "\
                "	where  pb.date_start between startdate and stopdate "\
                "	and pb.active=TRUE "\
                "	and state='complete' "\
                "	group by sa.name,to_char(pb.date_start,'Mon YYYY'),to_char(pb.date_start,'YYMM'); "\
                "	 "\
                "	CREATE TABLE RAINSLIPPERY AS	 "\
                "	select "\
                "	to_char(date,'YYMM') Date2, "\
                "	to_char(date,'Mon YYYY') Date, "\
                "	rs.iup, "\
                "	'RAINSLIPPERY' Sub_Activity, "\
                "	'RAINSLIPPERY' Remark, "\
                "	sum(total) RS "\
                "	from "\
                "	( "\
                "	select  "\
                "	d.date_act date, "\
                "	cp.name iup, "\
                "	pt.name Keterangan, "\
                "	s.name Shift, avg(d.volume) Total  "\
                "	from act_delay d "\
                "	left join res_company cp on d.bu_company_id=cp.id "\
                "	left join product_product pp on pp.id=d.product "\
                "	left join product_template pt on pt.id=pp.product_tmpl_id "\
                "	left join master_shift s on d.shift_id=s.id "\
                "	where d.date_act between startdate and stopdate "\
                "	and pt.name in ('RAIN','SLIPPERY') "\
                "	and d.active=true "\
                "	and d.state='complete' "\
                "	group by  "\
                "	cp.name, "\
                "	pt.name, "\
                "	s.name, "\
                "	d.date_act "\
                "	order by date_act,shift "\
                "	)rs "\
                "	group by to_char(date,'YYMM'), "\
                "	to_char(date,'Mon YYYY'),rs.iup "\
                "	union all "\
                "	select "\
                "	to_char(date,'YYMM') Date2, "\
                "	to_char(date,'Mon YYYY') Date, "\
                "	rs3.iup,sub_activity, 'RAINSLIPPERY' Remark, sum(rs) rs "\
                "	from( "\
                "		select date, 'Bhakti Coal Resources' iup, sub_activity, avg(rs) rs  "\
                "		from( "\
                "			select "\
                "			Date, "\
                "			rs.iup, "\
                "			'RAINSLIPPERY' Sub_Activity, "\
                "			sum(total) RS "\
                "			from "\
                "			( "\
                "			select  "\
                "			d.date_act date, "\
                "			cp.name iup, "\
                "			pt.name Keterangan, "\
                "			s.name Shift, avg(d.volume) Total  "\
                "			from act_delay d "\
                "			left join res_company cp on d.bu_company_id=cp.id "\
                "			left join product_product pp on pp.id=d.product "\
                "			left join product_template pt on pt.id=pp.product_tmpl_id "\
                "			left join master_shift s on d.shift_id=s.id "\
                "			where d.date_act between startdate and stopdate "\
                "			and pt.name in ('RAIN','SLIPPERY') "\
                "			and d.active=true "\
                "			and d.state='complete' "\
                "			group by  "\
                "			cp.name, "\
                "			pt.name, "\
                "			s.name, "\
                "			d.date_act "\
                "			order by date_act,shift "\
                "			)rs "\
                "			group by Date,rs.iup "\
                "		)rs2 group by date, sub_activity "\
                "	)rs3 group by to_char(date,'YYMM'), "\
                "	to_char(date,'Mon YYYY'), "\
                "	rs3.iup,sub_activity; "\
                "	CREATE TABLE RESUME AS "\
                "	select datafull.DATE2,datafull.DATE,datafull.iup,datafull.sub_activity, "\
                "	max(case when datafull.Remark='PLAN' then datafull.volume end) Plan, "\
                "	max(case when datafull.Remark='AKTUAL' then datafull.volume end) Aktual, "\
                "	rsfull.rs RS "\
                "	from( "\
                "		select date2,date,dat.iup,sub_activity,'AKTUAL' Remark,volume from  "\
                "		( "\
                "			select * from prod_akt "\
                "			union all "\
                "			select * from hauling_akt "\
                "			union all "\
                "			select * from barging_akt "\
                "		)dat "\
                "		left join master_sub_activity msa on msa.active=true and msa.name=dat.sub_activity "\
                "		where msa.id in (activity) "\
                " "\
                "		union all "\
                " "\
                "		select date2,date,dat.iup,sub_activity,'PLAN' Remark,volume from  "\
                "		( "\
                "			select * from prod_plan "\
                "			union all "\
                "			select * FROM HAULING_PLAN "\
                "			union all "\
                "			select * from barging_plan "\
                "		)dat "\
                "		left join master_sub_activity msa on msa.active=true and msa.name=dat.sub_activity "\
                "		where msa.id in (activity) "\
                "	)DATAFULL "\
                "	left join  "\
                "	( "\
                "		select * FROM RAINSLIPPERY "\
                "	)RSFULL ON RSFULL.date2=datafull.date2 and rsfull.iup=datafull.iup "\
                "	left join res_company cp on cp.active=true and cp.name=datafull.iup "\
                "	where cp.id = any(bisnis_unit) "\
                "	group by datafull.DATE2,datafull.DATE,datafull.iup,datafull.sub_activity,rsfull.rs "\
                "	order by sub_activity,date2	; "\
                "END$$; "\
                "select  "\
                "date2,date,iup, "\
                "case when sub_activity ='HAULING ROM TO PORT' then 'COAL HAULING' else sub_activity end sub_activity, "\
                "plan,aktual,rs "\
                "from resume "

        # query = " select * from(" \
        #         " select to_char(ap.date_act,'YYMM') Date2,to_char(ap.date_act,'Month YYYY') Date,cp.name IUP,sa.name Sub_Activity,sum(ap.volume) volume" \
        #         " from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date('"+date_start+"') and date('"+date_end+"') and ap.active=TRUE and state='complete' group by cp.name,sa.name,to_char(ap.date_act,'Month YYYY'),to_char(ap.date_act,'YYMM')" \
        #         " union all " \
        #         " select to_char(ap.date_act,'YYMM') Date2,to_char(ap.date_act,'Month YYYY') Date,'Bhakti Coal Resources' IUP,sa.name Sub_Activity,sum(ap.volume) volume" \
        #         " from act_production ap left join master_sub_activity sa on sa.id = ap.sub_activity_id left join res_company cp on ap.bu_company_id = cp.id" \
        #         " where  ap.date_act between date('"+date_start+"') and date('"+date_end+"') and ap.active=TRUE and state='complete' group by sa.name,to_char(ap.date_act,'Month YYYY'),to_char(ap.date_act,'YYMM')" \
        #         " union all" \
        #         " select to_char(ah.date_act,'YYMM') Date2,to_char(ah.date_act,'Month YYYY') Date,cp.name IUP,sa.name Sub_Activity,sum(ah.volume) volume" \
        #         " from act_hauling ah left join master_sub_activity sa on sa.id = ah.sub_activity_id left join res_company cp on ah.bu_company_id = cp.id" \
        #         " where  ah.date_act between date('"+date_start+"') and date('"+date_end+"') and ah.active=TRUE and state='complete' group by cp.name,sa.name,to_char(ah.date_act,'Month YYYY'),to_char(ah.date_act,'YYMM')" \
        #         " union all" \
        #         " select to_char(ah.date_act,'YYMM') Date2,to_char(ah.date_act,'Month YYYY') Date,'Bhakti Coal Resources' IUP,sa.name Sub_Activity,sum(ah.volume) volume" \
        #         " from act_hauling ah left join master_sub_activity sa on sa.id = ah.sub_activity_id left join res_company cp on ah.bu_company_id = cp.id" \
        #         " where  ah.date_act between date('"+date_start+"') and date('"+date_end+"') and ah.active=TRUE and state='complete' group by sa.name,to_char(ah.date_act,'Month YYYY'),to_char(ah.date_act,'YYMM')" \
        #         " union all " \
        #         " select to_char(ab.date_act,'YYMM') Date2,to_char(ab.date_act,'Month YYYY') Date,cp.name IUP,sa.name Sub_Activity,sum(ab.volume) volume" \
        #         " from act_barging ab left join master_sub_activity sa on sa.id = ab.sub_activity_id left join res_company cp on ab.bu_company_id = cp.id" \
        #         " where  ab.date_act between date('"+date_start+"') and date('"+date_end+"') and ab.active=TRUE and state='complete' group by cp.name,sa.name,to_char(ab.date_act,'Month YYYY'),to_char(ab.date_act,'YYMM')" \
        #         " union all select to_char(ab.date_act,'YYMM') Date2,to_char(ab.date_act,'Month YYYY') Date,'Bhakti Coal Resources' IUP,sa.name Sub_Activity,sum(ab.volume) volume" \
        #         " from act_barging ab left join master_sub_activity sa on sa.id = ab.sub_activity_id left join res_company cp on ab.bu_company_id = cp.id" \
        #         " where  ab.date_act between date('"+date_start+"') and date('"+date_end+"') and ab.active=TRUE and state='complete' group by sa.name,to_char(ab.date_act,'Month YYYY'),to_char(ab.date_act,'YYMM')" \
        #         " union all" \
        #         " select to_char(date,'YYMM') Date2,to_char(date,'Month YYYY') Date,iup,'RAINSLIPPERY' Sub_Activity,sum(total) RS" \
        #         " from(select d.date_act date,cp.name iup,pt.name Keterangan,s.name Shift, avg(d.volume) Total " \
        #         " from act_delay d left join res_company cp on d.bu_company_id=cp.id left join product_product pp on pp.id=d.product left join product_template pt on pt.id=pp.product_tmpl_id left join master_shift s on d.shift_id=s.id" \
        #         " where d.date_act between date('"+date_start+"') and date('"+date_end+"') and pt.name in ('RAIN','SLIPPERY') and d.active=true and d.state='complete' group by cp.name,pt.name,s.name,d.date_act order by date_act,shift)rs group by to_char(date,'YYMM'),to_char(date,'Month YYYY'),iup" \
        #         " union all " \
        #         " select to_char(date,'YYMM') Date2,to_char(date,'Month YYYY') Date,iup,sub_activity, sum(rs) rs" \
        #         " from(select date, 'Bhakti Coal Resources' iup, sub_activity, avg(rs) rs from(" \
        #         " select Date,iup,'RAINSLIPPERY' Sub_Activity,sum(total) RS from(select d.date_act date,cp.name iup,pt.name Keterangan,s.name Shift, avg(d.volume) Total " \
        #         " from act_delay d left join res_company cp on d.bu_company_id=cp.id left join product_product pp on pp.id=d.product left join product_template pt on pt.id=pp.product_tmpl_id left join master_shift s on d.shift_id=s.id" \
        #         " where d.date_act between date('"+date_start+"') and date('"+date_end+"') and pt.name in ('RAIN','SLIPPERY') and d.active=true and d.state='complete' group by  cp.name,pt.name,s.name,d.date_act order by date_act,shift)rs group by Date,iup)rs2 group by date, sub_activity) rs3 group by to_char(date,'YYMM'), to_char(date,'Month YYYY'), iup,sub_activity order by Sub_Activity,iup,Date2 " \
        #         " )DATAFULL " \
        #         " where iup='Bhumi Sriwijaya Perdana Coal'"
        return query

    def QueryPTDailySubActivity(self, yearmonth, bu_id, sub_activity):
        # date_start = date_start.replace("-", "")
        # date_end = date_end.replace("-", "")
        # bu_id = request.env['res.company'].sudo().search([('id', '=', bu_id)]).name
        bu_id = ",".join([str(elem) for elem in bu_id])
        query = "DO $$ "\
                "DECLARE startdate date; stopdate date; bisnis_unit integer[]; activity integer;yearmonth integer; "\
                "BEGIN "\
                "	select '"+yearmonth+"' into yearmonth; "\
                "	select array["+bu_id+"] into bisnis_unit; "\
                "	select '"+sub_activity+"' into activity; "\
                "	SELECT to_date(concat(yearmonth),'YYYYMMDD') INTO startdate; "\
                "	SELECT date(date(date_trunc('month', to_date(concat(yearmonth),'YYYYMMDD'))) + interval '1 month' - interval '1 day') INTO stopdate; "\
                "	DROP TABLE IF EXISTS prod_akt; "\
                "	DROP TABLE IF EXISTS hauling_akt; "\
                "	DROP TABLE IF EXISTS barging_akt; "\
                "	DROP TABLE IF EXISTS prod_plan; "\
                "	DROP TABLE IF EXISTS hauling_plan; "\
                "	DROP TABLE IF EXISTS barging_plan; "\
                "	DROP TABLE IF EXISTS RAINSLIPPERY; "\
                "	DROP TABLE IF EXISTS RESUME; "\
                "	CREATE TABLE PROD_AKT AS "\
                "	select  "\
                "	ap.date_act Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ap.volume) volume "\
                "	 from act_production ap "\
                "	left join master_sub_activity sa on sa.id = ap.sub_activity_id "\
                "	left join res_company cp on ap.bu_company_id = cp.id "\
                "	where  ap.date_act between startdate and stopdate "\
                "	and ap.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name,ap.date_act "\
                "	union all "\
                "	select  "\
                "	ap.date_act Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ap.volume) volume "\
                "	 from act_production ap "\
                "	left join master_sub_activity sa on sa.id = ap.sub_activity_id "\
                "	left join res_company cp on ap.bu_company_id = cp.id "\
                "	where  ap.date_act between startdate and stopdate "\
                "	and ap.active=TRUE "\
                "	and state='complete' "\
                "	group by sa.name,ap.date_act; "\
                "	CREATE TABLE HAULING_AKT AS "\
                "	select  "\
                "	ah.date_act Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ah.volume) volume "\
                "	 from act_hauling ah "\
                "	left join master_sub_activity sa on sa.id = ah.sub_activity_id "\
                "	left join res_company cp on ah.bu_company_id = cp.id "\
                "	where  ah.date_act between startdate and stopdate "\
                "	and ah.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name,ah.date_act "\
                "	union all "\
                "	select  "\
                "	ah.date_act Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ah.volume) volume "\
                "	 from act_hauling ah "\
                "	left join master_sub_activity sa on sa.id = ah.sub_activity_id "\
                "	left join res_company cp on ah.bu_company_id = cp.id "\
                "	where  ah.date_act between startdate and stopdate "\
                "	and ah.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by sa.name,ah.date_act; "\
                "	CREATE TABLE BARGING_AKT AS "\
                "	select  "\
                "	ab.date_act Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ab.volume) volume "\
                "	 from act_barging ab "\
                "	left join master_sub_activity sa on sa.id = ab.sub_activity_id "\
                "	left join res_company cp on ab.bu_company_id = cp.id "\
                "	where  ab.date_act between startdate and stopdate "\
                "	and ab.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name,ab.date_act "\
                "	union all "\
                "	select  "\
                "	ab.date_act Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ab.volume) volume "\
                "	 from act_barging ab "\
                "	left join master_sub_activity sa on sa.id = ab.sub_activity_id "\
                "	left join res_company cp on ab.bu_company_id = cp.id "\
                "	where  ab.date_act between startdate and stopdate "\
                "	and ab.active=TRUE "\
                "	and state='complete' "\
                "	group by sa.name,ab.date_act; "\
                "	CREATE TABLE PROD_PLAN AS "\
                "	select  "\
                "	pp.date_start Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(pp.volume_plan) volume "\
                "	 from planning_production pp "\
                "	left join master_sub_activity sa on sa.id = pp.sub_activity_id "\
                "	left join res_company cp on pp.bu_company_id = cp.id "\
                "	where  pp.date_start between startdate and stopdate "\
                "	and pp.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name,pp.date_start "\
                "	union all "\
                "	select  "\
                "	pp.date_start Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(pp.volume_plan) volume "\
                "	 from planning_production pp "\
                "	left join master_sub_activity sa on sa.id = pp.sub_activity_id "\
                "	left join res_company cp on pp.bu_company_id = cp.id "\
                "	where  pp.date_start between startdate and stopdate "\
                "	and pp.active=TRUE "\
                "	and state='complete' "\
                "	group by sa.name,pp.date_start;	 "\
                "	CREATE TABLE HAULING_PLAN AS "\
                "	select  "\
                "	ph.date_start Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ph.volume_plan) volume "\
                "	 from planning_hauling ph "\
                "	left join master_sub_activity sa on sa.id = ph.sub_activity_id "\
                "	left join res_company cp on ph.bu_company_id = cp.id "\
                "	where  ph.date_start between startdate and stopdate "\
                "	and ph.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by cp.name,sa.name,ph.date_start "\
                "	union all "\
                "	select  "\
                "	ph.date_start Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(ph.volume_plan) volume "\
                "	 from planning_hauling ph "\
                "	left join master_sub_activity sa on sa.id = ph.sub_activity_id "\
                "	left join res_company cp on ph.bu_company_id = cp.id "\
                "	where  ph.date_start between startdate and stopdate "\
                "	and ph.active=TRUE "\
                "	and state='complete' "\
                "	and sa.name='HAULING ROM TO PORT' "\
                "	group by sa.name,ph.date_start; "\
                "	CREATE TABLE BARGING_PLAN AS "\
                "	select  "\
                "	pb.date_start Date, "\
                "	cp.name IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(pb.volume_plan) volume "\
                "	 from planning_barging pb "\
                "	left join master_sub_activity sa on sa.id = pb.sub_activity_id "\
                "	left join res_company cp on pb.bu_company_id = cp.id "\
                "	where  pb.date_start between startdate and stopdate "\
                "	and pb.active=TRUE "\
                "	and state='complete' "\
                "	group by cp.name,sa.name,pb.date_start "\
                "	union all "\
                "	select  "\
                "	pb.date_start Date, "\
                "	'Bhakti Coal Resources' IUP, "\
                "	sa.name Sub_Activity, "\
                "	sum(pb.volume_plan) volume "\
                "	 from planning_barging pb "\
                "	left join master_sub_activity sa on sa.id = pb.sub_activity_id "\
                "	left join res_company cp on pb.bu_company_id = cp.id "\
                "	where  pb.date_start between startdate and stopdate "\
                "	and pb.active=TRUE "\
                "	and state='complete' "\
                "	group by sa.name,pb.date_start; "\
                "	CREATE TABLE RAINSLIPPERY AS	 "\
                "	select "\
                "	Date, "\
                "	iup, "\
                "	'RAINSLIPPERY' Sub_Activity, "\
                "	'RAINSLIPPERY' REMARK, "\
                "	sum(total) RS "\
                "	from "\
                "	( "\
                "	select  "\
                "	d.date_act date, "\
                "	cp.name iup, "\
                "	pt.name Keterangan, "\
                "	s.name Shift, avg(d.volume) Total  "\
                "	from act_delay d "\
                "	left join res_company cp on d.bu_company_id=cp.id "\
                "	left join product_product pp on pp.id=d.product "\
                "	left join product_template pt on pt.id=pp.product_tmpl_id "\
                "	left join master_shift s on d.shift_id=s.id "\
                "	where d.date_act between startdate and stopdate "\
                "	and pt.name in ('RAIN','SLIPPERY') "\
                "	and d.active=true "\
                "	and d.state='complete' "\
                "	group by  "\
                "	cp.name, "\
                "	pt.name, "\
                "	s.name, "\
                "	d.date_act "\
                "	order by date_act,shift "\
                "	)rs "\
                "	group by Date,iup "\
                "	union all "\
                "	select date, 'Bhakti Coal Resources' iup, sub_activity,	'RAINSLIPPERY' REMARK, avg(rs) rs  "\
                "	from( "\
                "		select "\
                "		Date, "\
                "		iup, "\
                "		'RAINSLIPPERY' Sub_Activity, "\
                "		sum(total) RS "\
                "		from "\
                "		( "\
                "		select  "\
                "		d.date_act date, "\
                "		cp.name iup, "\
                "		pt.name Keterangan, "\
                "		s.name Shift, avg(d.volume) Total  "\
                "		from act_delay d "\
                "		left join res_company cp on d.bu_company_id=cp.id "\
                "		left join product_product pp on pp.id=d.product "\
                "		left join product_template pt on pt.id=pp.product_tmpl_id "\
                "		left join master_shift s on d.shift_id=s.id "\
                "		where d.date_act between startdate and stopdate "\
                "		and pt.name in ('RAIN','SLIPPERY') "\
                "		and d.active=true "\
                "		and d.state='complete' "\
                "		group by  "\
                "		cp.name, "\
                "		pt.name, "\
                "		s.name, "\
                "		d.date_act "\
                "		order by date_act,shift "\
                "		)rs "\
                "		group by Date,iup "\
                "	)rs2 group by date, sub_activity; "\
                "	CREATE TABLE RESUME AS "\
                "	SELECT FULLDATA.date,FULLDATA.iup,FULLDATA.sub_activity, "\
                "	max(case when FULLDATA.remark='PLAN' then FULLDATA.volume END) Plan, "\
                "	max(case when FULLDATA.remark='AKTUAL' then FULLDATA.volume END) Aktual, "\
                "	RSFULL.RS RS "\
                "	FROM  "\
                "	( "\
                "		select date,iup,sub_activity,'AKTUAL' remark,volume from  "\
                "		( "\
                "			select * from prod_akt "\
                "			union all "\
                "			select * from hauling_akt "\
                "			union all "\
                "			select * from barging_akt "\
                "		)datas "\
                "		left join master_sub_activity msa on msa.active=true and msa.name=datas.sub_activity "\
                "		where msa.id in (activity) "\
                "		union all "\
                "		select date,iup,sub_activity,'PLAN' remark,volume from  "\
                "		( "\
                "			select * from prod_plan "\
                "			union all "\
                "			select * from hauling_plan "\
                "			union all "\
                "			select * from barging_plan "\
                "		)datas "\
                "		left join master_sub_activity msa on msa.active=true and msa.name=datas.sub_activity "\
                "		where msa.id in (activity) "\
                "	)FULLDATA "\
                "	LEFT JOIN  "\
                "	( "\
                "		select * from rainslippery "\
                "	)RSFULL ON RSFULL.IUP=FULLDATA.IUP AND RSFULL.DATE=FULLDATA.DATE "\
                "	left join res_company cp on cp.active=true and cp.name=FULLDATA.iup "\
                "	where cp.id = any(bisnis_unit) "\
                "	GROUP BY FULLDATA.date,FULLDATA.iup,FULLDATA.sub_activity,RSFULL.RS	; "\
                "END$$; "\
                "select  "\
                "date,iup, "\
                "case when sub_activity ='HAULING ROM TO PORT' then 'COAL HAULING' else sub_activity end sub_activity, "\
                "plan, aktual, rs "\
                "from resume "
        return query

class BcrQeuryJettyActivity(Exception):

    def QueryJettyActivity(self, bu_id):
        bu_id = ",".join([str(elem) for elem in bu_id])
        query = '''
                    DO $$
                    declare iup integer[];
                    BEGIN
                        select array[%s] into iup;
                        DROP TABLE IF EXISTS view_barge;
                        CREATE TABLE view_barge AS
                        select 
                        bu.code,
                        case when mv.name isnull then concat('SINGLE BARGE ->',mb.nama_barge) else mv.name end MV,
                        cp.name Buyer,
                        je.name Jetty,
                        seq_barge, 
                        lot, 
                        sum(volume) volume,max(date_act) date
                        from act_barging b
                        left join res_partner cp on b.buyer_id= cp.id and cp.active=true
                        left join master_mv mv on mv.id=b.mv_boat_id and mv.active=true
                        left join master_jetty je on je.id=b.jetty_id and je.active=true
                        left join master_barge mb on mb.active=true and b.barge_id=mb.id
                        LEFT JOIN res_company com ON com.active = true AND b.bu_company_id = com.id
                        left join master_bisnis_unit bu on bu.active=true and com.name=bu.name 
                        where b.active=TRUE
                        and b.state='complete'
                        and com.id = any(iup)
                        group by case when mv.name isnull then concat('SINGLE BARGE ->',mb.nama_barge) else mv.name end,
                        cp.name,
                        je.name,
                        seq_barge,
                        lot,
                        bu.code;
                    END $$;
                    select case when date < current_date - INTEGER '1' then 'Last Barging' else concat('MV ',mv) end mv,
                    case when date < current_date - INTEGER '1' then to_char(date,'DD Mon YYYY') else buyer end buyer,jetty,seq_barge,
                    case when date < current_date - INTEGER '1' then '' else 
                        (case when lot='LOKAL' then lot when lot is null then lot else concat('lot ',lot) end) end lot,
                    case when date < current_date - INTEGER '1' then 0 else volume end volume
                    ,date from 
                    (
                        select mv,buyer,jetty,seq_barge,lot,volume,date 
                        from view_barge
                        where concat(jetty,date) in 
                            (
                            select concat(jetty,max(date)) idjet
                            from view_barge
                            group by jetty
                            )
                        order by jetty
                    )jetfix
                    left join (select cp.name iup,j.* from master_jetty j
                    left join res_company cp on j.bu_company_id=cp.id and j.active=true
                    where j.active=true) iup on jetfix.jetty=iup.name
                    where 
                    concat(jetty,volume) in 
                        (
                        select concat(jetty, max(volume)) idjetfix
                        from view_barge
                        where concat(jetty,date) in 
                            (
                            select concat(jetty,max(date)) idjet
                            from view_barge
                            group by jetty
                            )
                        group by jetty
                        order by jetty
                        )
                ''' % (bu_id)

        return query

    def QueryJettyPieChart(self, date_start, date_end, bu_id):
        date_start = date_start.replace("-", "")
        date_end = date_end.replace("-", "")
        bu_id = ",".join([str(elem) for elem in bu_id])
        # ======== Update 4 Aug 2023
        query = '''
        DO $$
            declare iup integer[]; startdate date; stopdate date;

            BEGIN

                select %s into startdate;
                select %s into stopdate;
                select array[%s] into iup;

                DROP TABLE IF EXISTS jetty_update;

                create table jetty_update as

                select
                bu.code iup,
                je.name Jetty,
                sum(volume) volume
                from act_barging b
                left join master_jetty je on je.id=b.jetty_id and je.active=true
                left join res_company cp on je.bu_company_id = cp.id
                left join master_bisnis_unit bu on bu.active=true and cp.name=bu.name 
                where b.active=TRUE
                and b.state='complete'
                and b.date_act between startdate and stopdate
                and b.bu_company_id= any(iup)
                group by
                je.name,bu.code;

            end$$;


            select iup,jetty,volume, volume/(select sum(volume) from jetty_update) ach
            from jetty_update
        ''' % (date_start, date_end, bu_id)
        # ===============================
        # query = '''
        #             DO $$
        #                 declare iup integer[]; startdate date; stopdate date;
        #                 BEGIN
        #                     select %s into startdate;
        #                     select %s into stopdate;
        #                     select array[%s] into iup;
        #                     DROP TABLE IF EXISTS jetty_update;	
        #                     create table jetty_update as 
        #                     select
        #                     bu.code iup,
        #                     je.name Jetty,
        #                     sum(volume) volume
        #                     from act_barging b
        #                     left join master_jetty je on je.id=b.jetty_id and je.active=true
        #                     left join res_company cp on je.bu_company_id = cp.id
        #                     left join master_bisnis_unit bu on bu.active=true and cp.name=bu.name 
        #                     where b.active=TRUE
        #                     and b.state='complete'
        #                     and b.date_act between startdate and stopdate
        #                     and b.bisnis_unit_id = any(iup)
        #                     group by 
        #                     je.name,bu.code;
        #                 end$$;
        #                 select iup,jetty,volume, volume/(select sum(volume) from jetty_update) ach
        #                 from jetty_update
        #                 ''' % (date_start,date_end,bu_id)
        return query

class BcrQeuryShippingUpdate(Exception):

    def QuerySUTableUpdate(self):
        query = "SELECT buyer_name,market, "\
                "case when mother_vessel isnull then 'SINGLE BARGE' else mother_vessel end mother_vessel, "\
                "sum(volume) volume,to_char(max(last_date),'dd Mon yyyy') last_date "\
                "from "\
                "	( "\
                "	select "\
                "	seq_barge id_sell, "\
                "	cp.name buyer_name, "\
                "	mv.name mother_vessel, "\
                "	ba.nama_barge barge_name, "\
                "	je.name Jetty_name, "\
                "	initcap(b.market) market, "\
                "	sum(volume) Volume, "\
                "	max(date_act)  last_date "\
                "	 from act_barging b "\
                "	left join res_partner cp on b.buyer_id= cp.id "\
                "	left join master_mv mv on mv.id=b.mv_boat_id "\
                "	left join master_barge ba on b.barge_id=ba.id "\
                "	left join master_jetty je on b.jetty_id=je.id "\
                "	where b.active=TRUE "\
                "	and b.state='complete' "\
                "	group by b.buyer_id,mv.name,b.seq_barge,cp.name,b.market,ba.nama_barge,je.name "\
                "	order by  max(date_act) desc "\
                "	)data "\
                "group by buyer_name,market,case when mother_vessel isnull then to_char(id_sell,'FM9999') else mother_vessel end "\
                ",case when mother_vessel isnull then 'SINGLE BARGE' else mother_vessel end "\
                "order by max(last_date) desc "\
                "limit 10"
        # query = "select cp.name buyer_name,mv.name mother_vessel,ba.nama_barge barge_name,je.name Jetty_name,initcap(b.market) market,sum(volume) Volume,to_char ( max(date_act), 'dd Mon yyyy')  last_date" \
        #         " from act_barging b left join res_partner cp on b.buyer_id= cp.id left join master_mv mv on mv.id=b.mv_boat_id left join master_barge ba on b.barge_id=ba.id left join master_jetty je on b.jetty_id=je.id" \
        #         " where b.active=TRUE and b.state='complete' group by b.buyer_id,mv.name,b.seq_barge,cp.name,b.market,ba.nama_barge,je.name order by  max(date_act) desc limit 10"
        return query

    def QuerySUDMOperIUP(self):
        query = "select bisnis_unit,max(case when market='Export' then volume end) Export,max(case when market='Domestic' then volume end) Domestic,max(case when market='Domestic' then volume end) / (max(case when market='Domestic' then volume end)+max(case when market='Export' then volume end)) DMO" \
                " from(select cp.name bisnis_unit,initcap(b.market) market,sum(volume) Volume" \
                " from act_barging b left join master_mv mv on mv.id=b.mv_boat_id left join master_barge ba on b.barge_id=ba.id left join master_jetty je on b.jetty_id=je.id left join res_company cp on b.bu_company_id=cp.id " \
                " where b.active=TRUE and b.state='complete' and b.date_act between date(date_trunc('year', current_date - INTEGER '1')) and current_date - INTEGER '1' group by cp.name,b.market)dmo group by bisnis_unit"
        return query

class BcrQeuryRealtimeCoalbyWeighbridge(Exception):

    def QueryRealtimeLastDay(self, bu_id):
        bu_arr = bu_id
        bu_id = "','".join([str(elem) for elem in bu_id])
        bcr_query = "union all "\
                    "select "\
                    "'Bhakti Coal Resources' as name, "\
                    "'BCR' as code, "\
                    "tanggal,  "\
                    "sum(val_timbangan)/1000 volume "\
                    "from timbangan_vdata tim "\
                    "left join master_bisnis_unit bu on bu.active=true and tim.bisnis_unit=bu.code  "\
                    "left join res_company cp on cp.active=true and cp.name=bu.name "\
                    "where tanggal = current_date - INTEGER '1' "\
                    "group by  "\
                    "tanggal "\
                    "order by tanggal"

        if len(bu_arr) == 1:
                bcr_query = ""

        query = "DO $$ "\
                "declare iup integer[]; "\
                "BEGIN select array['"+str(bu_id)+"'] into iup;	 "\
                "DROP TABLE IF EXISTS view_timbangan;	 "\
                "CREATE TABLE view_timbangan AS "\
                "select "\
                "cp.name, "\
                "bu.code, "\
                "tanggal,  "\
                "sum(val_timbangan)/1000 volume "\
                "from timbangan_vdata tim "\
                "left join master_bisnis_unit bu on bu.active=true and tim.bisnis_unit=bu.code  "\
                "left join res_company cp on cp.active=true and cp.name=bu.name "\
                "where tanggal = current_date - INTEGER '1' "\
                "and cp.id = any(iup) "\
                "group by  "\
                "bisnis_unit, "\
                "tanggal,bu.name, bu,code,cp.name "\
                ""+bcr_query+" ; "\
                "END $$; "\
                "SELECT * FROM VIEW_TIMBANGAN "
        return query

    def QueryRealtimeToday(self, bu_id):
        bu_arr = bu_id
        bu_id = "','".join([str(elem) for elem in bu_id])
        bcr_query = "union all "\
                    "select "\
                    "'Bhakti Coal Resources' as name,"\
                    "'BCR' as code, "\
                    "tanggal, "\
                    "sum(val_timbangan)/1000 volume "\
                    "from timbangan_vdata tim "\
                    "left join master_bisnis_unit bu on bu.active=true and tim.bisnis_unit=bu.code "\
                    "left join res_company cp on cp.active=true and cp.name=bu.name "\
                    "where tanggal = current_date "\
                    "group by "\
                    "tanggal "\
                    "order by tanggal"

        if len(bu_arr) == 1:
                bcr_query = ""

        query = "DO $$ "\
                "declare iup integer[]; "\
                "BEGIN "\
                "select array['"+str(bu_id)+"'] into iup;	"\
                "DROP TABLE IF EXISTS view_timbangan; "\
                "CREATE TABLE view_timbangan AS "\
                "select "\
                "cp.name, "\
                "bu.code, "\
                "tanggal, "\
                "sum(val_timbangan)/1000 volume "\
                "from timbangan_vdata tim "\
                "left join master_bisnis_unit bu on bu.active=true and tim.bisnis_unit=bu.code "\
                "left join res_company cp on cp.active=true and cp.name=bu.name "\
                "where tanggal = current_date "\
                "and cp.id = any(iup) "\
                "group by "\
                "bisnis_unit,"\
                "tanggal,bu.name, bu,code,cp.name " \
                "" + bcr_query + " ; " \
                "END $$; "\
                "SELECT * FROM VIEW_TIMBANGAN "
        return query

    def QueryRealtimeTrendPerDay(self, bu_id):
        bu_arr = bu_id
        bu_id = "','".join([str(elem) for elem in bu_id])
        bcr_query = '''
            union all

            select
            'Bhakti Coal Resources' as name,
            'BCR' as code,
            tanggal,
            sum(val_timbangan)/1000 volume
            from timbangan_vdata tim
            left join master_bisnis_unit bu on bu.active=true and tim.bisnis_unit=bu.code
            left join res_company cp on cp.active=true and cp.name=bu.name
            where tanggal between date(current_date - INTEGER '13') and current_date
            and cp.id = any(iup)
            group by
            tanggal
            order by tanggal
        '''
        # bcr_query = "union all "\
        #             "select "\
        #             "'Bhakti Coal Resources' as name, "\
        #             "'BCR' as code, "\
        #             "tanggal,  "\
        #             "sum(val_timbangan)/1000 volume "\
        #             "from timbangan_vdata tim "\
        #             "left join master_bisnis_unit bu on bu.active=true and tim.bisnis_unit=bu.code  "\
        #             "left join res_company cp on cp.active=true and cp.name=bu.name "\
        #             "where tanggal between date(current_date - INTEGER '13') and current_date  "\
        #             "and cp.id = any(iup) "\
        #             "group by  "\
        #             "bisnis_unit, "\
        #             "tanggal,bu.name, bu,code,cp.name "\
        #             "order by tanggal"\

        if len(bu_arr) == 1:
                bcr_query = " "

        # ============ 4 Aug 2023
        query = '''
        DO $$
        declare iup integer[];

        BEGIN

            select array['%s'] into iup;

            DROP TABLE IF EXISTS view_timbangan;

            CREATE TABLE view_timbangan AS

        select
        cp.name,
        bu.code,
        tanggal,
        sum(val_timbangan)/1000 volume
        from timbangan_vdata tim
        left join master_bisnis_unit bu on bu.active=true and tim.bisnis_unit=bu.code
        left join res_company cp on cp.active=true and cp.name=bu.name
        where tanggal between date(current_date - INTEGER '13') and current_date
        and cp.id = any(iup)
        group by
        bisnis_unit,
        tanggal,bu.name, bu,code,cp.name
        %s;
        END $$;


        SELECT * FROM VIEW_TIMBANGAN
        ''' % (bu_id, bcr_query)
        # ===============================
        # query = "DO $$ "\
        #         "declare iup integer[]; "\
        #         "BEGIN  "\
        #         "select array['"+str(bu_id)+"'] into iup;	 "\
        #         "DROP TABLE IF EXISTS view_timbangan; "\
        #         "CREATE TABLE view_timbangan AS "\
        #         "select "\
        #         "cp.name, "\
        #         "bu.code, "\
        #         "tanggal,  "\
        #         "sum(val_timbangan)/1000 volume "\
        #         "from timbangan_vdata tim "\
        #         "left join master_bisnis_unit bu on bu.active=true and tim.bisnis_unit=bu.code  "\
        #         "left join res_company cp on cp.active=true and cp.name=bu.name "\
        #         "where tanggal between date(current_date - INTEGER '13') and current_date  "\
        #         "and cp.id = any(iup) "\
        #         "group by  "\
        #         "bisnis_unit, "\
        #         "tanggal,bu.name, bu,code,cp.name " \
        #         "" + bcr_query + " ; " \
        #         "END $$; "\
        #         "SELECT * FROM VIEW_TIMBANGAN "

        return query
