from odoo.addons.bcr_api_sh.controllers.query_dashboard import BcrQeuryResume, BcrQeuryRangkingBU, BcrQeuryRangkingKontraktor, BcrQeuryBestAchivement, BcrQeuryProductTrend, BcrQeuryJettyActivity, BcrQeuryShippingUpdate, BcrQeuryInventoryUpdate
from odoo.http import request


class QeuryResumeMiners(BcrQeuryResume):

    def QueryTableOverview(self, date, bu_id):
        dashboard = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan_prod;
                DROP TABLE IF EXISTS akt_prod;
                DROP TABLE IF EXISTS plan_barg;
                DROP TABLE IF EXISTS akt_barg;

                create table plan_prod as
                select
                'PLAN' item,
                sum(plan.volume_cg) volume_cg,
                sum(plan.volume_ob) volume_ob,
                sum(plan.volume_ch) volume_ch
                from plan_production_daily_valid plan
                left join res_company cp on plan.iup = cp.name
                where
                plan.date = tgl
                and cp.id  = any(id_iup);

                create table plan_barg as
                select
                sum(pb.volume_cb) volume_cb
                from plan_barging_daily pb
                left join res_company cp on pb.iup = cp.name
                where
                pb.date = tgl
                and cp.id  = any(id_iup);

                create table akt_prod as
                select distinct ms.name item,aktu.volume_cg,aktu.volume_ob,aktu.volume_ch,rs.vol_rainslip from master_shift ms
                left join (
                    select
                    upper(akt.shift) item,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    left join res_company cp on akt.iup = cp.name
                    where
                    akt.date = tgl
                    and cp.id  = any(id_iup)
                    group by upper(akt.shift)
                    )aktu on aktu.item=ms.name
                left join (
                select date,shift, avg(vol_rainslip) vol_rainslip
                from(
                    select
                    iup,date,upper(shift) shift, avg(vol_rainslip) vol_rainslip
                    from aktual_rainslip_daily rs
                    left join res_company cp on rs.iup = cp.name
                    where
                    rs.date = tgl
                    and cp.id  = any(id_iup)
                    group by iup,date,upper(shift)
                    )rs_iup
                group by date,shift
                )rs on ms.name=rs.shift
                where ms.active=true;

                create table akt_barg as
                select
                ab.shift,
                sum(ab.volume_cb) volume_cb
                from aktual_barging ab
                left join res_company cp on ab.iup = cp.name
                where
                ab.loading_date = tgl
                and cp.id  = any(id_iup)
                group by ab.shift;

            end$$;

            select item,volume_cg coal_getting,volume_ob overburden,volume_ob/volume_cg Stripping_Ratio,
            vol_rainslip rain_slippery,volume_ch coal_hauling , volume_cb coal_barging
            from akt_prod ap
            left join akt_barg ab on ap.item=ab.shift

            union all

            select 'AKTUAL'item,sum(volume_cg),sum(volume_ob),sum(volume_ob)/sum(volume_cg) Stripping_Ratio,
            sum(vol_rainslip),sum(volume_ch) ,sum(volume_cb) coal_barging
            from akt_prod ap
            left join akt_barg ab on ap.item=ab.shift

            union all

            select item,volume_cg,volume_ob,volume_ob/volume_cg Stripping_Ratio,
            null,volume_ch ,volume_cb
            from plan_prod
            left join plan_barg on 1=1
        ''' % (date, bu_id)
        return dashboard

    def QueryCGMTD(self, date, bu_id):
        query = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan_mtd;
                DROP TABLE IF EXISTS plan_eom;
                DROP TABLE IF EXISTS aktual_mtd;

                create table plan_mtd as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb from (
                    select
                    'PLAN MTD' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                  )pb on 1=1

                ;

                create table plan_eom as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
                from (
                    select
                    'PLAN EOM' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('month', tgl)) and date(date_trunc('month', tgl) + interval '1 month' - interval '1 day') 
                    and cp.id  = any (id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where 
                    pb.date between date(date_trunc('month', tgl)) and date(date_trunc('month', tgl) + interval '1 month' - interval '1 day')
                    and cp.id  = any(id_iup)
                    )pb on 1=1
                    ;

                create table aktual_mtd as
                select ap.item,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL MTD' item,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    left join res_company cp on akt.iup = cp.name
                    where
                    akt.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ap
                left join (
                    select
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    left join res_company cp on ab.iup = cp.name
                    where
                    ab.loading_date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ab on 1=1

                ;

            end$$;

            select item,volume_cg val from plan_mtd
            UNION ALL
            select item,volume_cg from plan_eom
            union all
            select item,volume_cg from aktual_mtd
            union all
            select 'PLAN SR' item,volume_ob/volume_cg sr from plan_mtd
            union all
            select 'AKTUAL SR' item,volume_ob/volume_cg sr from aktual_mtd
        ''' % (date, bu_id)
        return query

    def QueryCGYTD(self, date, bu_id):
        query = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan_ytd;
                DROP TABLE IF EXISTS plan_eoy;
                DROP TABLE IF EXISTS aktual_ytd;

                create table plan_ytd as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb from (
                    select
                    'PLAN YTD' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    ) pp
                left join (select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                  )pb on 1=1
                ;

                create table plan_eoy as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
                from (
                    select
                    'PLAN EOY' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('year', tgl)) and date(date_trunc('year', tgl) + interval '1 year' - interval '1 day') 
                    and cp.id  = any (id_iup)
                    ) pp
                left join (select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('year', tgl)) and date(date_trunc('year', tgl) + interval '1 year' - interval '1 day')
                    and cp.id  = any(id_iup)
                    )pb on 1=1
                    ;

                create table aktual_ytd as
                select ap.item,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL YTD' item,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    left join res_company cp on akt.iup = cp.name
                    where
                    akt.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ap
                left join (
                    select
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    left join res_company cp on ab.iup = cp.name
                    where
                    ab.loading_date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ab on 1=1

                ;

            end$$;

            select item,volume_cg val from plan_ytd
            UNION ALL
            select item,volume_cg from plan_eoy
            union all
            select item,volume_cg from aktual_ytd
            union all
            select 'PLAN SR' item,volume_ob/volume_cg sr from plan_ytd
            union all
            select 'AKTUAL SR' item,volume_ob/volume_cg sr from aktual_ytd
        ''' % (date, bu_id)
        return query

    def QueryOBMTD(self, date, bu_id):
        query = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan_mtd;
                DROP TABLE IF EXISTS plan_eom;
                DROP TABLE IF EXISTS aktual_mtd;

                create table plan_mtd as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb from (
                    select
                    'PLAN MTD' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where 
                    pb.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                  )pb on 1=1

                ;

                create table plan_eom as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
                from (
                    select 
                    'PLAN EOM' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where 
                    plan.date between date(date_trunc('month', tgl)) and date(date_trunc('month', tgl) + interval '1 month' - interval '1 day') 
                    and cp.id  = any (id_iup)
                    ) pp
                left join (select 
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where 
                    pb.date between date(date_trunc('month', tgl)) and date(date_trunc('month', tgl) + interval '1 month' - interval '1 day')
                    and cp.id  = any(id_iup)
                    )pb on 1=1
                    ;

                create table aktual_mtd as
                select ap.item,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL MTD' item,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    left join res_company cp on akt.iup = cp.name
                    where
                    akt.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ap
                left join (
                    select
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    left join res_company cp on ab.iup = cp.name
                    where
                    ab.loading_date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ab on 1=1

                ;

            end$$;

            select item,volume_ob val from plan_mtd
            UNION ALL
            select item,volume_ob from plan_eom
            union all
            select item,volume_ob from aktual_mtd
        ''' % (date, bu_id)
        return query

    def QueryOBYTD(self, date, bu_id):
        query = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan_ytd;
                DROP TABLE IF EXISTS plan_eoy;
                DROP TABLE IF EXISTS aktual_ytd;

                create table plan_ytd as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb from (
                    select
                    'PLAN YTD' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                )pb on 1=1

                ;

                create table plan_eoy as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
                from (
                    select
                    'PLAN EOY' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('year', tgl)) and date(date_trunc('year', tgl) + interval '1 year' - interval '1 day') 
                    and cp.id  = any (id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('year', tgl)) and date(date_trunc('year', tgl) + interval '1 year' - interval '1 day')
                    and cp.id  = any(id_iup)
                    )pb on 1=1
                    ;

                create table aktual_ytd as
                select ap.item,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL YTD' item,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    left join res_company cp on akt.iup = cp.name
                    where
                    akt.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ap
                left join (
                    select
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    left join res_company cp on ab.iup = cp.name
                    where
                    ab.loading_date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ab on 1=1

                ;

            end$$;

            select item,volume_ob val from plan_ytd
            UNION ALL
            select item,volume_ob from plan_eoy
            union all
            select item,volume_ob from aktual_ytd
        ''' % (date, bu_id)
        return query

    def QueryHaulingMTD(self, date, bu_id):
        query = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
            SELECT '%s' INTO tgl;
            SELECT array%s INTO id_iup;
            DROP TABLE IF EXISTS plan_mtd;
            DROP TABLE IF EXISTS plan_eom;
            DROP TABLE IF EXISTS aktual_mtd;

            create table plan_mtd as
            select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb from (
                select
                'PLAN MTD' item,
                sum(plan.volume_cg) volume_cg,
                sum(plan.volume_ob) volume_ob,
                sum(plan.volume_ch) volume_ch
                from plan_production_daily_valid plan
                left join res_company cp on plan.iup = cp.name
                where
                plan.date between date(date_trunc('month', tgl)) and tgl
                and cp.id  = any(id_iup)
                ) pp
            left join (
                select
                sum(pb.volume_cb) volume_cb
                from plan_barging_daily pb
                left join res_company cp on pb.iup = cp.name
                where
                pb.date between date(date_trunc('month', tgl)) and tgl
                and cp.id  = any(id_iup)
                )pb on 1=1

            ;

            create table plan_eom as
            select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
            from (
                select
                'PLAN EOM' item,
                sum(plan.volume_cg) volume_cg,
                sum(plan.volume_ob) volume_ob,
                sum(plan.volume_ch) volume_ch
                from plan_production_daily_valid plan
                left join res_company cp on plan.iup = cp.name
                where
                plan.date between date(date_trunc('month', tgl)) and date(date_trunc('month', tgl) + interval '1 month' - interval '1 day') 
                and cp.id  = any (id_iup)
                ) pp
            left join (
                select
                sum(pb.volume_cb) volume_cb
                from plan_barging_daily pb
                left join res_company cp on pb.iup = cp.name
                where
                pb.date between date(date_trunc('month', tgl)) and date(date_trunc('month', tgl) + interval '1 month' - interval '1 day')
                and cp.id  = any(id_iup)
                )pb on 1=1
            ;

            create table aktual_mtd as
            select ap.item,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
            from (
                select
                'AKTUAL MTD' item,
                sum(akt.volume_cg) volume_cg,
                sum(akt.volume_ob) volume_ob,
                sum(akt.volume_ch) volume_ch
                from aktual_production_daily akt
                left join res_company cp on akt.iup = cp.name
                where
                akt.date between date(date_trunc('month', tgl)) and tgl
                and cp.id  = any(id_iup)
                )ap
            left join (
                select
                sum(ab.volume_cb) volume_cb
                from aktual_barging ab
                left join res_company cp on ab.iup = cp.name
                where
                ab.loading_date between date(date_trunc('month', tgl)) and tgl
                and cp.id  = any(id_iup)
                )ab on 1=1

            ;

            end$$;

            select item,volume_ch val from plan_mtd
            UNION ALL
            select item,volume_ch from plan_eom
            union all
            select item,volume_ch from aktual_mtd
        ''' % (date, bu_id)
        return query

    def QueryHaulingYTD(self, date, bu_id):
        query = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan_ytd;
                DROP TABLE IF EXISTS plan_eoy;
                DROP TABLE IF EXISTS aktual_ytd;

                create table plan_ytd as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb from (
                    select
                    'PLAN YTD' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                  )pb on 1=1

                ;

                create table plan_eoy as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
                from (
                    select
                    'PLAN EOY' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('year', tgl)) and date(date_trunc('year', tgl) + interval '1 year' - interval '1 day') 
                    and cp.id  = any (id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('year', tgl)) and date(date_trunc('year', tgl) + interval '1 year' - interval '1 day')
                    and cp.id  = any(id_iup)
                    )pb on 1=1
                    ;

                create table aktual_ytd as
                select ap.item,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL YTD' item,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    left join res_company cp on akt.iup = cp.name
                    where
                    akt.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ap
                left join (
                    select
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    left join res_company cp on ab.iup = cp.name
                    where
                    ab.loading_date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ab on 1=1

                ;

            end$$;

            select item,volume_ch val from plan_ytd
            UNION ALL
            select item,volume_ch from plan_eoy
            union all
            select item,volume_ch from aktual_ytd
        ''' % (date, bu_id)
        return query

    def QueryBargingMTD(self, date, bu_id):
        query = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan_mtd;
                DROP TABLE IF EXISTS plan_eom;
                DROP TABLE IF EXISTS aktual_mtd;

                create table plan_mtd as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb from (
                    select
                    'PLAN MTD' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    ) pp
                left join (
                    select 
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where 
                    pb.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                  )pb on 1=1

                ;

                create table plan_eom as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
                from (
                    select
                    'PLAN EOM' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('month', tgl)) and date(date_trunc('month', tgl) + interval '1 month' - interval '1 day') 
                    and cp.id  = any (id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('month', tgl)) and date(date_trunc('month', tgl) + interval '1 month' - interval '1 day')
                    and cp.id  = any(id_iup)
                    )pb on 1=1
                    ;

                create table aktual_mtd as
                select ap.item,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL MTD' item,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    left join res_company cp on akt.iup = cp.name
                    where
                    akt.date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ap
                left join (
                    select
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    left join res_company cp on ab.iup = cp.name
                    where
                    ab.loading_date between date(date_trunc('month', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ab on 1=1

                ;

            end$$;

            select item,volume_cb val from plan_mtd
            UNION ALL
            select item,volume_cb from plan_eom
            union all
            select item,volume_cb from aktual_mtd
        ''' % (date, bu_id)
        return query

    def QueryBargingYTD(self, date, bu_id):
        query = '''
            DO $$
            DECLARE tgl date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO tgl;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan_ytd;
                DROP TABLE IF EXISTS plan_eoy;
                DROP TABLE IF EXISTS aktual_ytd;

                create table plan_ytd as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb from (
                    select
                    'PLAN YTD' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where
                    pb.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                  )pb on 1=1

                ;

                create table plan_eoy as
                select pp.item,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
                from (
                    select
                    'PLAN EOY' item,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    left join res_company cp on plan.iup = cp.name
                    where
                    plan.date between date(date_trunc('year', tgl)) and date(date_trunc('year', tgl) + interval '1 year' - interval '1 day') 
                    and cp.id  = any (id_iup)
                    ) pp
                left join (
                    select
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    left join res_company cp on pb.iup = cp.name
                    where 
                    pb.date between date(date_trunc('year', tgl)) and date(date_trunc('year', tgl) + interval '1 year' - interval '1 day')
                    and cp.id  = any(id_iup)
                    )pb on 1=1
                    ;

                create table aktual_ytd as
                select ap.item,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL YTD' item,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    left join res_company cp on akt.iup = cp.name
                    where
                    akt.date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ap
                left join (
                    select
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    left join res_company cp on ab.iup = cp.name
                    where
                    ab.loading_date between date(date_trunc('year', tgl)) and tgl
                    and cp.id  = any(id_iup)
                    )ab on 1=1

                ;

            end$$;

            select item,volume_cb val from plan_ytd
            UNION ALL
            select item,volume_cb from plan_eoy
            union all
            select item,volume_cb from aktual_ytd
        ''' % (date, bu_id)
        return query


class QeuryRankingBUMiners(BcrQeuryRangkingBU):

    def QueryRBUTable(self, date_start, date_end):
        query = '''
            DO $$
            DECLARE startdate date; stopdate date;

            BEGIN
                SELECT '%s' INTO startdate;
                SELECT '%s' INTO stopdate;
                DROP TABLE IF EXISTS plan;
                DROP TABLE IF EXISTS aktual;

                create table plan as
                select pp.item,pp.iup,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb
                from (
                    select
                    'PLAN' item,
                    plan.iup iup,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    where
                    plan.date between startdate and stopdate
                    group by plan.iup
                    ) pp
                left join (
                    select
                    pb.iup iup,
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    where
                    pb.date between startdate and stopdate
                    group by pb.iup
                  )pb on pp.iup=pb.iup;

                create table aktual as
                select ap.item,ap.iup,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL' item,
                    akt.iup iup,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    where
                    akt.date between startdate and stopdate
                    group by akt.iup
                    )ap
                left join (
                    select
                    ab.iup iup,
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    where
                    ab.loading_date between startdate and stopdate
                    group by ab.iup
                    )ab on ap.iup=ab.iup;

            end$$;

            select bu.code iup,a.volume_cg/p.volume_cg COAL_GETTING,
            a.volume_ob/p.volume_ob OVERBURDEN,
            a.volume_ch/p.volume_ch COAL_HAULING,
            a.volume_cb/p.volume_cb COAL_BARGING
            from plan p
            full join
            (select 'PLAN' item,iup,volume_cg,volume_ob,volume_ch,volume_cb from aktual) a on p.item=a.item and p.iup=a.iup
            left join master_bisnis_unit bu on bu.active=true and a.iup=bu.name
        ''' % (date_start, date_end)
        return query


    def QueryGIUPPerSubActivity(self, date_start, date_end, sub_activity):
        sub_activity_id = request.env['master.sub.activity'].browse(int(sub_activity[0]))
        if sub_activity_id.name == 'HAULING ROM TO PORT':
            name = 'COAL HAULING'
        else:
            name = sub_activity_id.name

        query = '''
            DO $$
            DECLARE startdate date; stopdate date;
            activity text;

            BEGIN
                SELECT '%s' INTO startdate;
                SELECT '%s' INTO stopdate;
                select '%s' into activity;
                DROP TABLE IF EXISTS plan;
                DROP TABLE IF EXISTS aktual;
                DROP TABLE IF EXISTS results;

                create table plan as
                select pp.item,pp.iup,pp.volume_cg,pp.volume_ob,pp.volume_ch,pb.volume_cb 
                from (
                    select
                    'PLAN' item,
                    plan.iup iup,
                    sum(plan.volume_cg) volume_cg,
                    sum(plan.volume_ob) volume_ob,
                    sum(plan.volume_ch) volume_ch
                    from plan_production_daily_valid plan
                    where
                    plan.date between startdate and stopdate
                    group by plan.iup
                    ) pp
                left join (
                    select
                    pb.iup iup,
                    sum(pb.volume_cb) volume_cb
                    from plan_barging_daily pb
                    where
                    pb.date between startdate and stopdate
                    group by pb.iup
                  )pb on pp.iup=pb.iup;

                create table aktual as
                select ap.item,ap.iup,ap.volume_cg,ap.volume_ob,ap.volume_ch,ab.volume_cb
                from (
                    select
                    'AKTUAL' item,
                    akt.iup iup,
                    sum(akt.volume_cg) volume_cg,
                    sum(akt.volume_ob) volume_ob,
                    sum(akt.volume_ch) volume_ch
                    from aktual_production_daily akt
                    where
                    akt.date between startdate and stopdate
                    group by akt.iup
                    )ap
                left join (
                    select
                    ab.iup iup,
                    sum(ab.volume_cb) volume_cb
                    from aktual_barging ab
                    where
                    ab.loading_date between startdate and stopdate
                    group by ab.iup
                    )ab on ap.iup=ab.iup;

                create table results as
                select item, bu.code iup, activity sub_activity, case when activity = 'COAL GETTING' then volume_cg
                when activity = 'OVERBURDEN' then volume_ob
                when activity = 'COAL HAULING' then volume_ch
                when activity = 'COAL BARGING' then volume_cb
                else null end volume
                FROM (
                select * from plan
                union all
                select * from aktual
                    )res
                left join master_bisnis_unit bu on bu.active=true and res.iup=bu.name;

            end$$;

            select
            iup,sub_activity,
            sum(case when item = 'PLAN' then volume end) Plan,
            sum(case when item = 'AKTUAL' then volume end) Aktual
            from results
            group by iup,sub_activity
        ''' % (date_start, date_end, name)
        return query


class QueryRankingKontraktorMiners(BcrQeuryRangkingKontraktor):

    def QueryRKTable(self, date_start, date_end, bu_ids):
        query = '''
            DO $$
            DECLARE startdate date; stopdate date; id_iup integer[];

            BEGIN
                SELECT '%s' INTO startdate;
                SELECT '%s' INTO stopdate;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan;
                DROP TABLE IF EXISTS aktual;

                create table plan as
                select
                'PLAN' item,
                plan.kontraktor,
                sum(plan.volume_cg) volume_cg,
                sum(plan.volume_ob) volume_ob,
                sum(plan.volume_ch) volume_ch
                from plan_production_daily_valid plan
                left join res_company cp on plan.iup = cp.name
                where
                plan.date between startdate and stopdate
                and cp.id  = any(id_iup)
                group by plan.kontraktor;

                create table aktual as
                select
                'AKTUAL' item,
                akt.kontraktor,
                sum(akt.volume_cg) volume_cg,
                sum(akt.volume_ob) volume_ob,
                sum(akt.volume_ch) volume_ch
                from aktual_production_daily akt
                left join res_company cp on akt.iup = cp.name
                where
                akt.date between startdate and stopdate
                and cp.id  = any(id_iup)
                group by akt.kontraktor;

            end$$;


            select a.kontraktor,coalesce(a.volume_cg/nullif(p.volume_cg,0),0) COAL_GETTING,
            coalesce(a.volume_ob/nullif(p.volume_ob,0),0) OVERBURDEN,
            coalesce(a.volume_ch,0) COAL_HAULING
            from plan p
            full join
            (select 'PLAN' item,kontraktor,volume_cg,volume_ob,volume_ch from aktual) a on p.item=a.item and p.kontraktor=a.kontraktor
        ''' % (date_start, date_end, bu_ids)
        return query

    def QueryRKGraphic(self, date_start, date_end, bu_ids, sub_activity):
        sub_activity_id = request.env['master.sub.activity'].browse(int(sub_activity[0]))
        if sub_activity_id.name == 'HAULING ROM TO PORT':
            name = 'COAL HAULING'
        else:
            name = sub_activity_id.name
        query = '''
            DO $$
            DECLARE startdate date; stopdate date;
            activity text; id_iup integer[];

            BEGIN
                SELECT '%s' INTO startdate;
                SELECT '%s' INTO stopdate;
                select '%s' into activity;
                SELECT array%s INTO id_iup;
                DROP TABLE IF EXISTS plan;
                DROP TABLE IF EXISTS aktual;
                DROP TABLE IF EXISTS results;

                create table plan as
                select
                'PLAN' item,
                plan.kontraktor,
                sum(plan.volume_cg) volume_cg,
                sum(plan.volume_ob) volume_ob,
                sum(plan.volume_ch) volume_ch
                from plan_production_daily_valid plan
                left join res_company cp on plan.iup = cp.name
                where
                plan.date between startdate and stopdate
                and cp.id  = any(id_iup)
                group by plan.kontraktor;

                create table aktual as
                select
                'AKTUAL' item,
                akt.kontraktor,
                sum(akt.volume_cg) volume_cg,
                sum(akt.volume_ob) volume_ob,
                sum(akt.volume_ch) volume_ch
                from aktual_production_daily akt
                left join res_company cp on akt.iup = cp.name
                where
                akt.date between startdate and stopdate
                and cp.id  = any(id_iup)
                group by akt.kontraktor;

                create table results as
                select item, res.kontraktor, activity sub_activity, case when activity = 'COAL GETTING' then volume_cg
                when activity = 'OVERBURDEN' then volume_ob
                when activity = 'COAL HAULING' then volume_ch else null end volume
                FROM (
                select * from plan
                union all
                select * from aktual
                    )res;

            end$$;


            select
            kontraktor,sub_activity,
            sum(case when item = 'PLAN' then volume end) Plan,
            sum(case when item = 'AKTUAL' then volume end) Aktual
            from results
            where volume>0
            group by kontraktor,sub_activity

        ''' % (date_start, date_end, name, bu_ids)
        return query


class BcrQeuryBestAchivementMiners(BcrQeuryBestAchivement):

    def QueryPivotTableDaily(self, date_start, date_end, sub_activity):
        sub_activity_id = request.env['master.sub.activity'].browse(int(sub_activity[0]))
        if sub_activity_id.name == 'HAULING ROM TO PORT':
            name = 'COAL HAULING'
        else:
            name = sub_activity_id.name
        query = """
            DO $$
            DECLARE startdate date; stopdate date; activity text;

            BEGIN
                SELECT '%s' INTO startdate;
                SELECT '%s' INTO stopdate;
                SELECT '%s' INTO activity;

                DROP TABLE IF EXISTS akt;
                DROP TABLE IF EXISTS max_akt;

                CREATE TABLE akt AS
                select date,bu.code iup, sub_activity,volume

                from
                (
                    --OVERBURDEN
                    select
                    date,iup,'OVERBURDEN' sub_activity,sum(volume_ob) volume
                    from aktual_production_daily
                    group by date,iup,sub_activity

                    union all

                    --COAL GETTING
                    select
                    date,iup,'COAL GETTING' sub_activity,sum(volume_cg) volume
                    from aktual_production_daily
                    group by date,iup,sub_activity

                    union all

                    --COAL HAULING
                    select
                    date,iup,'COAL HAULING' sub_activity,sum(volume_ch) volume
                    from aktual_production_daily
                    group by date,iup,sub_activity

                    union all

                    --COAL BARGING
                    select loading_date,iup,'COAL BARGING' sub_activity, sum(volume_cb) volume
                    from aktual_barging
                    group by loading_date,iup,sub_activity
                )data
                left join master_bisnis_unit bu on bu.active=true and data.iup=bu.name
                where date between startdate and stopdate;

                CREATE TABLE max_akt AS
                
                select iup,sub_activity,max(volume) volume from akt
                --left join master_bisnis_unit bu on bu.active=true and akt.iup=bu.name 
                where sub_activity=activity
                group by iup,sub_activity;

            END $$;

            --select * from akt;

            select max(data.date),iup,sub_activity,volume from
                (select aa.date,bb.* from akt aa 
                left join max_akt bb on aa.iup=bb.iup and aa.sub_activity=bb.sub_activity and aa.volume=bb.volume
                where bb.iup is not null)data
            group by iup,sub_activity,volume
        """ % (date_start, date_end, name)
        return query

    def QueryPivotTableMonthly(self, date_start, date_end, sub_activity):
        sub_activity_id = request.env['master.sub.activity'].browse(int(sub_activity[0]))
        if sub_activity_id.name == 'HAULING ROM TO PORT':
            name = 'COAL HAULING'
        else:
            name = sub_activity_id.name
        query = """
            DO $$
            DECLARE startdate date; stopdate date; activity text;

            BEGIN
                SELECT '%s' INTO startdate;
                SELECT '%s' INTO stopdate;
                SELECT '%s' INTO activity;

                DROP TABLE IF EXISTS akt;
                DROP TABLE IF EXISTS max_akt;

                CREATE TABLE akt AS
                select date,bu.code iup, sub_activity,volume

                from
                (
                    --OVERBURDEN
                    select
                    to_char(date,'Month YYYY') date,iup,'OVERBURDEN' sub_activity,sum(volume_ob) volume
                    from aktual_production_daily
                    where date between startdate and stopdate
                    group by to_char(date,'Month YYYY'),iup,sub_activity

                    union all

                    --COAL GETTING
                    select
                    to_char(date,'Month YYYY') date,iup,'COAL GETTING' sub_activity,sum(volume_cg) volume
                    from aktual_production_daily
                    where date between startdate and stopdate
                    group by to_char(date,'Month YYYY'),iup,sub_activity

                    union all

                    --COAL HAULING
                    select
                    to_char(date,'Month YYYY') date,iup,'COAL HAULING' sub_activity,sum(volume_ch) volume
                    from aktual_production_daily
                    where date between startdate and stopdate
                    group by to_char(date,'Month YYYY'),iup,sub_activity

                    union all

                    --COAL BARGING
                    select to_char(loading_date,'Month YYYY') date,iup,'COAL BARGING' sub_activity, sum(volume_cb) volume
                    from aktual_barging
                    where loading_date between startdate and stopdate
                    group by to_char(loading_date,'Month YYYY'),iup,sub_activity
                )data
                left join master_bisnis_unit bu on bu.active=true and data.iup=bu.name
                ;

                CREATE TABLE max_akt AS

                select iup,sub_activity,max(volume) volume from akt
                --left join master_bisnis_unit bu on bu.active=true and akt.iup=bu.name
                where sub_activity=activity
                group by iup,sub_activity;

            END $$;

            --select * from akt;

            select aa.date,bb.* from akt aa left join max_akt bb on aa.iup=bb.iup and aa.sub_activity=bb.sub_activity and aa.volume=bb.volume
            where bb.iup is not null
        """ % (date_start, date_end, name)
        return query


class QeuryProductTrendMiners(BcrQeuryProductTrend):

    def QueryPTMonthlySubActivity(self, date_start, date_end, bu_id, sub_activity):
        bu_id = request.env['res.company'].browse(int(bu_id))
        sub_activity_id = request.env['master.sub.activity'].browse(int(sub_activity))
        if sub_activity_id.name == 'HAULING ROM TO PORT':
            name = 'COAL HAULING'
        else:
            name = sub_activity_id.name
        query = """
            DO $$
            DECLARE startdate date; stopdate date; bisnis_unit text; activity text;

            BEGIN
                SELECT '%s' INTO startdate;
                SELECT '%s' INTO stopdate;
                select '%s' into bisnis_unit;
                select '%s' into activity;

                DROP TABLE IF EXISTS prod_akt;
                DROP TABLE IF EXISTS hauling_akt;
                DROP TABLE IF EXISTS barging_akt;
                DROP TABLE IF EXISTS prod_plan;
                DROP TABLE IF EXISTS hauling_plan;
                DROP TABLE IF EXISTS barging_plan;
                DROP TABLE IF EXISTS RAINSLIPPERY;
                DROP TABLE IF EXISTS RESUME;

                CREATE TABLE PROD_AKT AS

                select
                to_char(ap.date,'YYMM') Date2,
                to_char(ap.date,'Mon YYYY') Date,
                IUP,
                sub_activity,
                CASE WHEN sub_activity = 'OVERBURDEN' THEN sum(volume_ob)
                     WHEN sub_activity = 'COAL GETTING' THEN sum(volume_cg)
                     WHEN sub_activity = 'COAL HAULING' THEN sum(volume_ch)
                END AS volume
                from aktual_production_daily ap
                cross join (select 'OVERBURDEN' as sub_activity
                            union all
                            select 'COAL GETTING' as sub_activity 
                            union all
                            select 'COAL HAULING' as sub_activity 
                           ) as activities
                where ap.date between startdate and stopdate
                group by to_char(ap.date,'YYMM'),iup,to_char(ap.date,'Mon YYYY'),sub_activity
                --order by date2

                union all
                
                    select 
                to_char(ap.date,'YYMM') Date2,
                to_char(ap.date,'Mon YYYY') Date,
                'Bhakti Coal Resources' IUP,
                sub_activity,
                CASE WHEN sub_activity = 'OVERBURDEN' THEN sum(volume_ob)
                     WHEN sub_activity = 'COAL GETTING' THEN sum(volume_cg)
                     WHEN sub_activity = 'COAL HAULING' THEN sum(volume_ch)
                END AS volume
                from aktual_production_daily ap
                cross join (select 'OVERBURDEN' as sub_activity 
                            union all
                            select 'COAL GETTING' as sub_activity 
                            union all
                            select 'COAL HAULING' as sub_activity 
                           ) as activities
                where ap.date between startdate and stopdate
                group by to_char(ap.date,'YYMM'),to_char(ap.date,'Mon YYYY'),sub_activity
                order by date2;

                
                CREATE TABLE BARGING_AKT AS
                select 
                to_char(ap.loading_date,'YYMM') Date2,
                to_char(ap.loading_date,'Mon YYYY') Date,
                IUP,
                'COAL BARGING' sub_activity,
                sum(volume_cb) AS volume
                from aktual_barging ap
                where loading_date between startdate and stopdate
                group by to_char(ap.loading_date,'YYMM'),to_char(ap.loading_date,'Mon YYYY'),sub_activity,iup
                --order by date2

                union all

                select 
                to_char(ap.loading_date,'YYMM') Date2,
                to_char(ap.loading_date,'Mon YYYY') Date,
                'Bhakti Coal Resources' IUP,
                'COAL BARGING' sub_activity,
                sum(volume_cb) AS volume
                from aktual_barging ap
                where loading_date between startdate and stopdate
                group by to_char(ap.loading_date,'YYMM'),to_char(ap.loading_date,'Mon YYYY'),sub_activity
                order by date2;
                
                CREATE TABLE PROD_PLAN AS
                select 
                to_char(ap.date,'YYMM') Date2,
                to_char(ap.date,'Mon YYYY') Date,
                IUP,
                sub_activity,
                CASE WHEN sub_activity = 'OVERBURDEN' THEN sum(volume_ob)
                     WHEN sub_activity = 'COAL GETTING' THEN sum(volume_cg)
                     WHEN sub_activity = 'COAL HAULING' THEN sum(volume_ch)
                END AS volume
                from plan_production_daily_valid ap
                cross join (select 'OVERBURDEN' as sub_activity 
                            union all
                            select 'COAL GETTING' as sub_activity 
                            union all
                            select 'COAL HAULING' as sub_activity 
                           ) as activities
                where ap.date between startdate and stopdate
                group by to_char(ap.date,'YYMM'),to_char(ap.date,'Mon YYYY'),sub_activity,iup
                --order by date2

                union all

                select 
                to_char(ap.date,'YYMM') Date2,
                to_char(ap.date,'Mon YYYY') Date,
                'Bhakti Coal Resources' IUP,
                sub_activity,
                CASE WHEN sub_activity = 'OVERBURDEN' THEN sum(volume_ob)
                     WHEN sub_activity = 'COAL GETTING' THEN sum(volume_cg)
                     WHEN sub_activity = 'COAL HAULING' THEN sum(volume_ch)
                END AS volume
                from plan_production_daily_valid ap
                cross join (select 'OVERBURDEN' as sub_activity 
                            union all
                            select 'COAL GETTING' as sub_activity 
                            union all
                            select 'COAL HAULING' as sub_activity 
                           ) as activities
                where ap.date between startdate and stopdate
                group by to_char(ap.date,'YYMM'),to_char(ap.date,'Mon YYYY'),sub_activity
                order by date2; 
                
                CREATE TABLE BARGING_PLAN AS
                select 
                to_char(ap.date,'YYMM') Date2,
                to_char(ap.date,'Mon YYYY') Date,
                IUP,
                'COAL BARGING' sub_activity,
                sum(volume_cb)
                from plan_barging_daily ap
                group by to_char(ap.date,'YYMM'),to_char(ap.date,'Mon YYYY'),iup
                --order by date2

                union all

                select 
                to_char(ap.date,'YYMM') Date2,
                to_char(ap.date,'Mon YYYY') Date,
                'Bhakti Coal Resources' IUP,
                'COAL BARGING' sub_activity,
                sum(volume_cb)
                from plan_barging_daily ap
                group by to_char(ap.date,'YYMM'),to_char(ap.date,'Mon YYYY')
                order by date2;
                
                CREATE TABLE RAINSLIPPERY AS    
                select
                to_char(date,'YYMM') Date2,
                to_char(date,'Mon YYYY') Date,
                rs.iup,
                'RAINSLIPPERY' Sub_Activity,
                'RAINSLIPPERY' Remark,
                sum(total) RS
                from
                (
                select 
                date,
                iup,
                shift,
                avg(vol_rainslip) Total 
                from aktual_rainslip_daily d
                where date between startdate and stopdate
                and vol_rainslip>0
                group by 
                date,iup,shift
                order by date
                )rs
                group by to_char(date,'YYMM'),
                to_char(date,'Mon YYYY'),rs.iup

                union all

                select
                to_char(date,'YYMM') Date2,
                to_char(date,'Mon YYYY') Date,
                iup,
                'RAINSLIPPERY' Sub_Activity,
                'RAINSLIPPERY' Remark,
                sum(total) RS
                from
                    (select date, 'Bhakti Coal Resources' iup, avg(total) total
                    from
                     (select date,iup,sum(total) total from
                        (
                        select 
                        date,
                        iup,
                        shift,
                        avg(vol_rainslip) Total 
                        from aktual_rainslip_daily d
                        where date between startdate and stopdate
                        and vol_rainslip>0
                        group by 
                        date,iup,shift
                        order by date
                        )rs
                      group by date, iup)rs2
                    group by date)rs3
                group by to_char(date,'YYMM'),
                to_char(date,'Mon YYYY'),iup;

                CREATE TABLE RESUME AS
                select datafull.DATE2,datafull.DATE,datafull.iup,datafull.sub_activity,
                max(case when datafull.Remark='PLAN' then datafull.volume end) Plan,
                max(case when datafull.Remark='AKTUAL' then datafull.volume end) Aktual,
                rsfull.rs RS

                from(
                    select date2,date,dat.iup,sub_activity,'AKTUAL' Remark,volume from 
                    (
                        select * from prod_akt
                        union all
                        select * from barging_akt
                    )dat
                    where sub_activity=activity

                    union all

                    select date2,date,dat.iup,sub_activity,'PLAN' Remark,volume from 
                    (
                        select * from prod_plan
                        union all
                        select * from barging_plan
                    )dat
                    where sub_activity=activity
                )DATAFULL
                left join 
                (
                    select * FROM RAINSLIPPERY
                )RSFULL ON RSFULL.date2=datafull.date2 and rsfull.iup=datafull.iup
                where datafull.iup=bisnis_unit
                group by datafull.DATE2,datafull.DATE,datafull.iup,datafull.sub_activity,rsfull.rs
                order by sub_activity,date2 ;
                
            END$$;


            select * from resume
        """ % (date_start, date_end, bu_id.name, name)
        return query

    def QueryPTDailySubActivity(self, yearmonth, bu_id, sub_activity):
        # bu_id = request.env['res.company'].browse(int(bu_id))
        # sub_activity_id = request.env['master.sub.activity'].browse(int(sub_activity[0]))
        query = """
            DO $$
            DECLARE startdate date; stopdate date; bisnis_unit integer; activity integer;yearmonth integer;

            BEGIN
                select '%s' into yearmonth;
                select '%s' into bisnis_unit;
                select '%s' into activity;
                SELECT to_date(concat(yearmonth),'YYYYMMDD') INTO startdate;
                SELECT date(date(date_trunc('month', to_date(concat(yearmonth),'YYYYMMDD'))) + interval '1 month' - interval '1 day') INTO stopdate;

                DROP TABLE IF EXISTS prod_akt;
                DROP TABLE IF EXISTS hauling_akt;
                DROP TABLE IF EXISTS barging_akt;
                DROP TABLE IF EXISTS prod_plan;
                DROP TABLE IF EXISTS hauling_plan;
                DROP TABLE IF EXISTS barging_plan;
                DROP TABLE IF EXISTS RAINSLIPPERY;
                DROP TABLE IF EXISTS RESUME;

                CREATE TABLE PROD_AKT AS
                    select
                    Date,
                    IUP,
                    sub_activity,
                    CASE WHEN sub_activity = 'OVERBURDEN' THEN sum(volume_ob)
                         WHEN sub_activity = 'COAL GETTING' THEN sum(volume_cg)
                         WHEN sub_activity = 'COAL HAULING' THEN sum(volume_ch)
                    END AS volume
                    from aktual_production_daily ap
                    cross join (select 'OVERBURDEN' as sub_activity
                                union all
                                select 'COAL GETTING' as sub_activity
                                union all
                                select 'COAL HAULING' as sub_activity
                               ) as activities
                    where ap.date between startdate and stopdate
                    group by Date,sub_activity,iup
                --order by date2

                union all

                    select
                    Date,
                    'Bhakti Coal Resources' IUP,
                    sub_activity,
                    CASE WHEN sub_activity = 'OVERBURDEN' THEN sum(volume_ob)
                         WHEN sub_activity = 'COAL GETTING' THEN sum(volume_cg)
                         WHEN sub_activity = 'COAL HAULING' THEN sum(volume_ch)
                    END AS volume
                    from aktual_production_daily ap
                    cross join (select 'OVERBURDEN' as sub_activity
                                union all
                                select 'COAL GETTING' as sub_activity
                                union all
                                select 'COAL HAULING' as sub_activity
                               ) as activities
                    where ap.date between startdate and stopdate
                    group by Date,sub_activity
                    order by Date;

                CREATE TABLE BARGING_AKT AS
                    select
                    loading_date Date,
                    IUP,
                    'COAL BARGING' sub_activity,
                    sum(volume_cb) AS volume
                    from aktual_barging ap
                    where loading_date between startdate and stopdate
                    group by loading_date,sub_activity,iup
                    --order by date2

                union all

                    select
                    loading_date Date,
                    'Bhakti Coal Resources' IUP,
                    'COAL BARGING' sub_activity,
                    sum(volume_cb) AS volume
                    from aktual_barging ap
                    where loading_date between startdate and stopdate
                    group by loading_date,sub_activity
                    order by Date;

                CREATE TABLE PROD_PLAN AS
                    select
                    Date,
                    IUP,
                    sub_activity,
                    CASE WHEN sub_activity = 'OVERBURDEN' THEN sum(volume_ob)
                         WHEN sub_activity = 'COAL GETTING' THEN sum(volume_cg)
                         WHEN sub_activity = 'COAL HAULING' THEN sum(volume_ch)
                    END AS volume
                    from plan_production_daily_valid ap
                    cross join (select 'OVERBURDEN' as sub_activity
                                union all
                                select 'COAL GETTING' as sub_activity
                                union all
                                select 'COAL HAULING' as sub_activity
                               ) as activities
                    where ap.date between startdate and stopdate
                    group by Date,sub_activity,iup
                    --order by date2

                union all

                    select
                    Date,
                    'Bhakti Coal Resources' IUP,
                    sub_activity,
                    CASE WHEN sub_activity = 'OVERBURDEN' THEN sum(volume_ob)
                         WHEN sub_activity = 'COAL GETTING' THEN sum(volume_cg)
                         WHEN sub_activity = 'COAL HAULING' THEN sum(volume_ch)
                    END AS volume
                    from plan_production_daily_valid ap
                    cross join (select 'OVERBURDEN' as sub_activity
                                union all
                                select 'COAL GETTING' as sub_activity
                                union all
                                select 'COAL HAULING' as sub_activity
                               ) as activities
                    where ap.date between startdate and stopdate
                    group by Date,sub_activity
                    order by Date;


                CREATE TABLE BARGING_PLAN AS
                    select
                    Date,
                    IUP,
                    'COAL BARGING' sub_activity,
                    sum(volume_cb) volume
                    from plan_barging_daily ap
                    group by Date,iup
                    --order by date2

                union all

                    select
                    Date,
                    'Bhakti Coal Resources' IUP,
                    'COAL BARGING' sub_activity,
                    sum(volume_cb) volume
                    from plan_barging_daily ap
                    group by Date
                    order by Date;

                CREATE TABLE RAINSLIPPERY AS
                    select
                    Date,
                    rs.iup,
                    'RAINSLIPPERY' Sub_Activity,
                    'RAINSLIPPERY' Remark,
                    sum(total) RS
                    from
                        (
                            select
                            date,
                            iup,
                            shift,
                            avg(vol_rainslip) Total
                            from aktual_rainslip_daily d
                            where date between startdate and stopdate
                            and vol_rainslip>0
                            group by
                            date,iup,shift
                            order by date
                        )rs
                    group by date,rs.iup

                union all

                select
                Date,
                iup,
                'RAINSLIPPERY' Sub_Activity,
                'RAINSLIPPERY' Remark,
                sum(total) RS
                from
                    (select date, 'Bhakti Coal Resources' iup, avg(total) total
                    from
                     (select date,iup,sum(total) total from
                        (
                        select
                        date,
                        iup,
                        shift,
                        avg(vol_rainslip) Total
                        from aktual_rainslip_daily d
                        where date between startdate and stopdate
                        and vol_rainslip>0
                        group by
                        date,iup,shift
                        order by date
                        )rs
                      group by date, iup)rs2
                    group by date)rs3
                group by date,iup;

                CREATE TABLE RESUME AS
                SELECT FULLDATA.date,FULLDATA.iup,FULLDATA.sub_activity,
                max(case when FULLDATA.remark='PLAN' then FULLDATA.volume END) Plan,
                max(case when FULLDATA.remark='AKTUAL' then FULLDATA.volume END) Aktual,
                RSFULL.RS RS
                FROM
                (
                    select date,iup,sub_activity,'AKTUAL' remark,volume from
                    (
                        select * from prod_akt
                        union all
                        select * from barging_akt
                    )datas
                    left join master_sub_activity msa on msa.active=true and msa.name=datas.sub_activity
                    where msa.id in (activity)

                    union all

                    select date,iup,sub_activity,'PLAN' remark,volume from
                    (
                        select * from prod_plan
                        union all
                        select * from barging_plan
                    )datas
                    left join master_sub_activity msa on msa.active=true and msa.name=datas.sub_activity
                    where msa.id in (activity)

                )FULLDATA
                LEFT JOIN
                (
                    select * from rainslippery
                )RSFULL ON RSFULL.IUP=FULLDATA.IUP AND RSFULL.DATE=FULLDATA.DATE
                left join res_company cp on cp.active=true and cp.name=FULLDATA.iup
                where cp.id in (bisnis_unit)
                GROUP BY FULLDATA.date,FULLDATA.iup,FULLDATA.sub_activity,RSFULL.RS ;

            END$$;


            select
            date,iup,
            case when sub_activity ='HAULING ROM TO PORT' then 'COAL HAULING' else sub_activity end sub_activity,
            plan, aktual, rs
            from resume
        """ % (yearmonth, bu_id, sub_activity)
        return query


class QeuryJettyActivityMiners(BcrQeuryJettyActivity):

    def QueryJettyActivity(self, bu_id):
        query = """
            DO $$
            declare iup integer[];

            BEGIN

                select array%s into iup;

                DROP TABLE IF EXISTS barge_lastday;
                DROP TABLE IF EXISTS barge_details;
                DROP TABLE IF EXISTS ops_1;
                DROP TABLE IF EXISTS ops_2;
                DROP TABLE IF EXISTS ops_3;
                DROP TABLE IF EXISTS last_barge;
                DROP TABLE IF EXISTS rank_help_1;
                DROP TABLE IF EXISTS rank_help_2;

                CREATE TABLE barge_lastday AS
                select company_id,loading_date,--upper(sh.ttype || ' SHIFT') AS shift,
                barge_detail_id,jetty_id,sum(volume) volume
                --tcb.*
                from product_detail tcb
                --LEFT JOIN master_shiftmode_line sh ON sh.id = tcb.shift_line_id
                WHERE tcb.active = true AND tcb.state= 'complete'
                and loading_date=current_date - INTEGER '1'
                and company_id = any(iup)
                group by loading_date,--upper(sh.ttype || ' SHIFT'),
                barge_detail_id,jetty_id,company_id
                order by jetty_id,loading_date desc--,upper(sh.ttype || ' SHIFT') desc
                ;

                CREATE TABLE barge_details AS
                select
                mv.name AS mv,
                barg.nama_barge AS barge,
                bd.buyer_id as buyer,
                --bd.*
                bd.id,bd.jetty_id,bd.company_id,bd.complete_date,bd.provisional_quantity,bd.status_jetty,bd.volume_est,bd.dsr_volume_barge
                from barge_detail bd
                LEFT JOIN master_jetty jet ON jet.id = bd.jetty_id
                LEFT JOIN master_mv mv ON mv.id = bd.mv_id
                LEFT JOIN master_barge barg ON barg.id = bd.barge_id
                left join res_partner buy on buy.id=bd.buyer_id
                WHERE bd.active = true
                --and bd.status_jetty='complete'
                and bd.company_id = any(iup)
                order by bd.jetty_id,bd.complete_date desc;
                
                CREATE TABLE ops_1 AS
                select 
                bd.mv,bd.barge,bd.buyer,jet.name jetty,bd.complete_date,bd.provisional_quantity plan_volume,bd.volume_est akt_volume_tc,bd.dsr_volume_barge akt_volume_dsr
                --bd.*,bl.volume
                from barge_details bd left join barge_lastday bl
                on bd.jetty_id=bl.jetty_id and bd.status_jetty<>'complete' and bd.id=bl.barge_detail_id
                LEFT JOIN master_jetty jet ON jet.id = bd.jetty_id
                where bl.volume is not null;

                CREATE TABLE ops_2 AS
                select
                bd.mv,bd.barge,bd.buyer,jet.name jetty,bd.complete_date,bd.provisional_quantity plan_volume,bd.volume_est akt_volume_tc,bd.dsr_volume_barge akt_volume_dsr
                --bd.*,bl.volume
                from barge_details bd left join barge_lastday bl
                on bd.jetty_id=bl.jetty_id and bd.status_jetty='complete' and bd.id=bl.barge_detail_id
                LEFT JOIN master_jetty jet ON jet.id = bd.jetty_id
                where bl.volume is not null;

                CREATE TABLE last_barge AS
                select
                bd.jetty_id,max(bd.complete_date) complete_date
                -- bd.*
                from barge_detail bd
                LEFT JOIN master_jetty jet ON jet.id = bd.jetty_id
                LEFT JOIN master_mv mv ON mv.id = bd.mv_id
                LEFT JOIN master_barge barg ON barg.id = bd.barge_id
                left join res_partner buy on buy.id=bd.buyer_id
                WHERE bd.active = true
                and bd.status_jetty='complete'
                and bd.company_id = any(iup)
                group by bd.jetty_id;

                CREATE TABLE ops_3 AS
                select
                bd.mv,bd.barge,bd.buyer,jet.name jetty,bd.complete_date,bd.provisional_quantity plan_volume,bd.volume_est akt_volume_tc,bd.dsr_volume_barge akt_volume_dsr
            --  bd.*,bl.complete_date cd
                from barge_details bd 
                left join last_barge bl
                on bd.jetty_id=bl.jetty_id and bd.status_jetty='complete' and bd.complete_date=bl.complete_date
                LEFT JOIN master_jetty jet ON jet.id = bd.jetty_id
                where bl.complete_date is not null;

                CREATE TABLE rank_help_1 AS
                select 1 ranks,* from ops_1
                union all
                select 2 ranks,* from ops_2
                union all
                select 3 ranks,* from ops_3;

                CREATE TABLE rank_help_2 AS
                select min(ranks) ranks,jetty
                    from rank_help_1
                group by jetty;

            END $$;

            select * from barge_details;
            select * from ops_1;
            select * from ops_2;
            select * from last_barge;
            select * from ops_3;
            select * from rank_help_2;

            select
            -- aa.*,
            aa.jetty,
            case when aa.ranks=3 then 'Last Barging' else
                (case when buy.kode_buyer is not null then buy.kode_buyer else buy.name end)
                end buyer,
            case when aa.ranks=3 then TO_CHAR(aa.complete_date, 'dd Mon yyyy')  else
                (case when aa.mv is null then 'BG ' || aa.barge else 'MV ' || aa.mv end)
                end carrier,
            case when aa.ranks=3 then aa.akt_volume_dsr else aa.akt_volume_tc end volume_aktual,
            case when aa.ranks=3 then aa.akt_volume_dsr else aa.akt_volume_tc end/aa.plan_volume ach
            from rank_help_1 aa left join rank_help_2 bb on aa.ranks=bb.ranks and aa.jetty=bb.jetty
            left join res_partner buy on buy.id=aa.buyer
            where bb.jetty is not null
        """ % (bu_id)
        return query

    def QueryJettyPieChart(self, date_start, date_end, bu_id):
        bu_id = ",".join([str(elem) for elem in bu_id])
        query = '''
            DO $$
            declare iups integer[]; startdate date; stopdate date;

            BEGIN

                select '%s' into startdate;
                select '%s' into stopdate;
                select array[%s] into iups;

                DROP TABLE IF EXISTS jetty_update;  

                create table jetty_update as

                select jetty,bu.code iup,sum(volume_cb) volume
                from aktual_barging ab
                left join res_company cp on cp.name=ab.iup
                left join master_bisnis_unit bu on  ab.iup=bu.name
                where loading_date between startdate and stopdate
                and cp.id = any(iups)
                and cp.active=true and bu.active=true
                group by jetty,bu.code;

            end$$;

            select * from jetty_update;
            select iup,jetty,volume, volume/(select sum(volume) from jetty_update) ach
            from jetty_update;
        ''' % (date_start, date_end, bu_id)
        return query


class QeuryOutlookMiners(Exception):

    def QueryOutlookPit(self):
        query = '''
            DO $$
            declare dates_c date;

            BEGIN
                select current_date - INTEGER '1' into dates_c;

                DROP TABLE IF EXISTS aktual;
                DROP TABLE IF EXISTS plan;
                DROP TABLE IF EXISTS outlook;

                create table aktual as
                select dates_c date_now,iup,pit, sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm 
                from aktual_production_daily
                where date between date(date_trunc('year', dates_c)) and dates_c
                group by iup,pit,to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by to_char(date,'yyyymm'),iup,pit;

                create table plan as
                select dates_c date_now,iup,pit, sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm  
                from plan_production_daily_valid
                where date > dates_c
                group by iup,pit,to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by to_char(date,'yyyymm'),iup,pit;

                create table outlook as
                select date_now,iup,pit,sum(volume) volume,mon_year,yyyymm
                from(
                        select * from aktual
                        union all
                        select * from plan
                    )data
                where yyyymm>=to_char(date_now,'yyyymm')
                group by date_now,iup,pit,mon_year,yyyymm
                order by yyyymm;

            end$$;


            select * from outlook
        '''
        return query

    def QueryOutlookMonthlyIup(self):
        query = '''
            DO $$
            declare dates_m date;

            BEGIN
                select current_date - INTEGER '1' into dates_m;

                DROP TABLE IF EXISTS aktual;
                DROP TABLE IF EXISTS plan;
                DROP TABLE IF EXISTS outlook;
                DROP TABLE IF EXISTS plan_bulan;

                create table aktual as
                select dates_m date_now,iup, sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm 
                from aktual_production_daily
                where date between date(date_trunc('year', dates_m)) and dates_m
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by to_char(date,'yyyymm'),iup;

                create table plan as
                select dates_m date_now,iup, sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm  
                from plan_production_daily_valid
                where date > dates_m
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by to_char(date,'yyyymm'),iup;

                create table outlook as
                select date_now,iup,sum(volume)volume,mon_year,yyyymm
                from(
                        select * from aktual
                        union all
                        select * from plan
                    )data
                where yyyymm>=to_char(date_now,'yyyymm')
                group by date_now,iup,mon_year,yyyymm
                order by yyyymm;

                create table plan_bulan as
                select dates_m date_now,iup, category,sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm  
                from plan_production_daily_valid
                where date between date(date_trunc('month', dates_m)) and date(date_trunc('month', dates_m)+ INTERVAL '1 month' - INTERVAL '1 day')
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm'),category
                order by to_char(date,'yyyymm'),iup;

            end$$;


            select
            pl.iup,pl.category,pl.volume plan, ou.volume aktual,ou.volume/pl.volume ach
            from plan_bulan pl
            left join outlook ou on ou.iup=pl.iup and pl.yyyymm=ou.yyyymm;

            select cp.name iup,pl.category,pl.volume plan_3mrp, ou.volume outlook,ou.volume/pl.volume ach from res_company cp
            left join plan_bulan pl on pl.iup=cp.name
            left join outlook ou on ou.iup=pl.iup and pl.yyyymm=ou.yyyymm
            where active=true
            and id in(1,4,2)
        '''
        return query

    def QueryOutlookYearlyIup(self):
        query = '''
            DO $$
            declare dates_y date;

            BEGIN
                select current_date - INTEGER '1' into dates_y;

                DROP TABLE IF EXISTS aktual;
                DROP TABLE IF EXISTS plan;
                DROP TABLE IF EXISTS outlook;
                DROP TABLE IF EXISTS plan_bulan;
                DROP TABLE IF EXISTS plan_RKAP;
                DROP TABLE IF EXISTS help;

                create table aktual as
                select dates_y date_now,iup, sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm 
                from aktual_production_daily
                where date between date(date_trunc('year', dates_y)) and dates_y
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by to_char(date,'yyyymm'),iup;

                create table plan as
                select dates_y date_now,iup, sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm  
                from plan_production_daily_valid
                where date > dates_y
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by to_char(date,'yyyymm'),iup;

                create table outlook as
                select date_now,iup,sum(volume)volume,mon_year,yyyymm
                from(
                        select * from aktual
                        union all
                        select * from plan
                    )data
            --  where yyyymm>=to_char(date_now,'yyyymm')
                group by date_now,iup,mon_year,yyyymm
                order by yyyymm;

                create table plan_bulan as
                select dates_y date_now,iup, category,sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm  
                from plan_production_daily_valid
                where date between date(date_trunc('year', dates_y)) and date(date_trunc('year', dates_y)+ INTERVAL '1 year' - INTERVAL '1 day')
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm'),category
                order by to_char(date,'yyyymm'),iup;

                create table plan_RKAP as
                SELECT
                 2 ranks,
                 to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm ,SUM(VOLUME_CG) volume
                   FROM ( SELECT to_date(((pp1.tahun_plan::text || '-'::text) || pp1.bulan_plan) || '-01'::text, 'YYYY-MM-DD'::text) AS plan_3mrp,
                            date_trunc('MONTH'::text, pp1.date::timestamp with time zone)::date AS datesss,
                            pp1.tahun_plan::text || pp1.bulan_plan AS plan_3mrp2,
                            pp1.plan_group_id,
                            pp1.category,
                            pp1.iup,
                            pp1.kontraktor,
                            pp1.activity,
                            pp1.pit,
                            pp1.source,
                            pp1.tahun_plan,
                            pp1.bulan_plan,
                            pp1.date,
                            pp1.volume_cg,
                            pp1.volume_ob,
                            pp1.volume_ch,
                            pp1.dist_cg,
                            pp1.dist_ob,
                            pp1.dist_ch,
                            pp2.batas_plan_3mrp,
                            pp2.kon2
                           FROM plan_production_daily pp1
                             LEFT JOIN ( SELECT to_char(max(to_date(((plan_production_daily.tahun_plan::text || '-'::text) || plan_production_daily.bulan_plan) || '-01'::text, 'YYYY-MM-DD'::text))::timestamp with time zone, 'YYYYMM'::text) AS batas_plan_3mrp,
                                    plan_production_daily.kontraktor AS kon2
                                   FROM plan_production_daily
                                  GROUP BY plan_production_daily.kontraktor) pp2 ON pp1.kontraktor::text = pp2.kon2::text) dat
                  WHERE dat.category::text = 'RKAP'::text
                group by to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by yyyymm;

                create table help as
                select min(ranks) ranks,mon_year,yyyymm
                from
                    (select 1 ranks, Mon_year,yyyymm, sum(volume) volume
                    from plan_bulan
                    group by Mon_year,yyyymm
                    union all
                    select * from plan_rkap)data
                group by mon_year,yyyymm
                order by yyyymm ;

            end$$;


            select h.mon_year,h.yyyymm,data.volume plan,case when data2.volume is null then data.volume else data2.volume end outlook from help h
                left join
                    (select 1 ranks, Mon_year,yyyymm, sum(volume) volume
                    from plan_bulan
                    group by Mon_year,yyyymm
                    union all
                    select * from plan_rkap)data on h.ranks=data.ranks and h.mon_year=data.mon_year
                left join (select mon_year,yyyymm,sum(volume)volume from outlook
                    group by mon_year,yyyymm
                    order by yyyymm)data2 on data2.yyyymm=h.yyyymm
            order by h.yyyymm;
        '''
        return query

    def QueryOutlookIup(self):
        query = '''
            DO $$
            declare dates_i date;

            BEGIN
                select current_date - INTEGER '1' into dates_i;

                DROP TABLE IF EXISTS aktual;
                DROP TABLE IF EXISTS plan;
                DROP TABLE IF EXISTS outlook;
                DROP TABLE IF EXISTS plan_bulan;
                DROP TABLE IF EXISTS plan_RKAP;
                DROP TABLE IF EXISTS help;

                create table aktual as
                select dates_i date_now,iup, sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm 
                from aktual_production_daily
                where date between date(date_trunc('year', dates_i)) and dates_i
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by to_char(date,'yyyymm'),iup;

                create table plan as
                select dates_i date_now,iup, sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm  
                from plan_production_daily_valid
                where date > dates_i
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm')
                order by to_char(date,'yyyymm'),iup;

                create table outlook as
                select date_now,iup,sum(volume)volume,mon_year,yyyymm
                from(
                        select * from aktual
                        union all
                        select * from plan
                    )data
            --  where yyyymm>=to_char(date_now,'yyyymm')
                group by date_now,iup,mon_year,yyyymm
                order by yyyymm;

                create table plan_bulan as
                select dates_i date_now,iup, category,sum(volume_cg) volume,to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm
                from plan_production_daily_valid
                where date between date(date_trunc('year', dates_i)) and date(date_trunc('year', dates_i)+ INTERVAL '1 year' - INTERVAL '1 day')
                group by iup,to_char(date,'Mon yyyy'),to_char(date,'yyyymm'),category,iup
                order by to_char(date,'yyyymm'),iup;

                create table plan_RKAP as
                SELECT
                 2 ranks,iup,
                 to_char(date,'Mon yyyy') Mon_year,to_char(date,'yyyymm') yyyymm ,SUM(VOLUME_CG) volume
                   FROM ( SELECT to_date(((pp1.tahun_plan::text || '-'::text) || pp1.bulan_plan) || '-01'::text, 'YYYY-MM-DD'::text) AS plan_3mrp,
                            date_trunc('MONTH'::text, pp1.date::timestamp with time zone)::date AS datesss,
                            pp1.tahun_plan::text || pp1.bulan_plan AS plan_3mrp2,
                            pp1.plan_group_id,
                            pp1.category,
                            pp1.iup,
                            pp1.kontraktor,
                            pp1.activity,
                            pp1.pit,
                            pp1.source,
                            pp1.tahun_plan,
                            pp1.bulan_plan,
                            pp1.date,
                            pp1.volume_cg,
                            pp1.volume_ob,
                            pp1.volume_ch,
                            pp1.dist_cg,
                            pp1.dist_ob,
                            pp1.dist_ch,
                            pp2.batas_plan_3mrp,
                            pp2.kon2
                           FROM plan_production_daily pp1
                             LEFT JOIN ( SELECT to_char(max(to_date(((plan_production_daily.tahun_plan::text || '-'::text) || plan_production_daily.bulan_plan) || '-01'::text, 'YYYY-MM-DD'::text))::timestamp with time zone, 'YYYYMM'::text) AS batas_plan_3mrp,
                                    plan_production_daily.kontraktor AS kon2
                                   FROM plan_production_daily
                                  GROUP BY plan_production_daily.kontraktor) pp2 ON pp1.kontraktor::text = pp2.kon2::text) dat
                  WHERE dat.category::text = 'RKAP'::text 
                group by to_char(date,'Mon yyyy'),to_char(date,'yyyymm'),iup
                order by yyyymm;

                create table help as
                select min(ranks) ranks,iup,mon_year,yyyymm
                from
                    (select 1 ranks,iup, Mon_year,yyyymm, sum(volume) volume
                    from plan_bulan
                    group by Mon_year,yyyymm,iup
                    union all
                    select * from plan_rkap)data
                group by mon_year,yyyymm,iup
                order by yyyymm ;

            end$$;


            select iup, sum(outlook) outlook
            from (
                select h.mon_year,h.iup,h.yyyymm,data.volume plan,case when data2.volume is null then data.volume else data2.volume end outlook from help h
                    left join
                        (select 1 ranks,iup, Mon_year,yyyymm, sum(volume) volume
                        from plan_bulan
                        group by Mon_year,yyyymm,iup
                        union all
                        select * from plan_rkap)data on h.ranks=data.ranks and h.mon_year=data.mon_year and h.iup=data.iup
                    left join (select iup,mon_year,yyyymm,sum(volume)volume from outlook
                        group by mon_year,yyyymm,iup
                        order by yyyymm)data2 on data2.yyyymm=h.yyyymm and data2.iup=h.iup
                )data group by iup;
        '''
        return query


class QueryJoinSurvey(Exception):

    def QuerySurveyCG(self, yearmonth, bu_id):
        query = """
            DO $$
            DECLARE bisnis_unit integer[]; yearmonth char(6);

            BEGIN
                select '%s' into yearmonth;
                select array%s into bisnis_unit;

                DROP TABLE IF EXISTS survey_cg;

                CREATE TABLE survey_cg AS
                select
                bu.code IUP,
                selected_years||left('0'||period_month,2) yyyymm,
                asl.track_count TC,
                asl.volume Survey
                from act_survey sur
                left join res_company cp on sur.company_id = cp.id
                left join master_bisnis_unit bu on bu.active=true and cp.name=bu.name
                left join act_survey_line asl on sur.id=asl.cg_survey_id
                where sur.active=true and state='complete'
                and selected_years||left('0'||period_month,2) = yearmonth
                and cp.id =any (bisnis_unit);

            END$$;

            select iup,yyyymm,sum(tc) TC, sum(survey) Survey,sum(survey)/sum(tc) Prosentase
            from survey_cg
            group by iup,yyyymm
        """ % (yearmonth, bu_id)
        return query

    def QuerySurveyOB(self, yearmonth, bu_id):
        query = """
            DO $$
            DECLARE bisnis_unit integer[]; yearmonth char(6);

            BEGIN
                select '%s' into yearmonth;
                select array%s into bisnis_unit;

                DROP TABLE IF EXISTS survey_ob;

                CREATE TABLE survey_ob AS
                select
                bu.code IUP,
                selected_years||left('0'||period_month,2) yyyymm,
                asl.track_count TC,
                asl.volume Survey
                from act_survey sur
                left join res_company cp on sur.company_id = cp.id
                left join master_bisnis_unit bu on bu.active=true and cp.name=bu.name
                left join act_survey_line asl on sur.id=asl.ob_survey_id
                where sur.active=true and state='complete'
                and selected_years||left('0'||period_month,2) = yearmonth
                and cp.id =any (bisnis_unit);

            END$$;

            select iup,yyyymm,sum(tc) TC, sum(survey) Survey,sum(survey)/sum(tc) Prosentase
            from survey_ob
            group by iup,yyyymm
        """ % (yearmonth, bu_id)
        return query


class QeuryShippingUpdate(BcrQeuryShippingUpdate):

    def QuerySUTableUpdate(self):
        query = """
            select
            rp.name buyer,
            ss.stowage_plan plan,
            coalesce(ab.actual/nullif(ss.stowage_plan,0),0) progress,
            case when ss.state='draft' then 'progress' else 'complete' end status,
            ab.* from (
                select
                    ab.shipping_id,
                    ab.market_type market,
                    max(ab.loading_date) last_barge,
                    sum(ab.volume_cb) actual
                    from aktual_barging ab
                    group by ab.shipping_id,ab.market_type
                )ab
            left join sales_shipping ss on ab.shipping_id=ss.id
            left join res_partner rp on rp.id=ss.buyer_id
            order by last_barge desc
        """
        return query

    def QuerySUDMOperIUP(self):
        query = """
            select
            bisnis_unit,
            max(case when market_type='domestic' then volume_cb end) domestic,
            max(case when market_type='export' then volume_cb end) export,
            plan_rkab.plan_rkab,
            max(case when market_type='domestic' then volume_cb end)/plan_rkab.plan_rkab DMO

            from (
                select
                ab.market_type,
                sum(ab.volume_cb) volume_cb,
                bu.code bisnis_unit
                from aktual_barging ab
                left join sales_shipping ss on ab.shipping_id=ss.id
                left join res_company cp on ss.company_id = cp.id
                left join master_bisnis_unit bu on bu.active=true and cp.name=bu.name 
                where loading_date between date(date_trunc('year', current_date - INTEGER '1')) and current_date - INTEGER '1'
                group by ab.market_type, bu.code
            )data
            left join (
                select
                bu.code IUP,SUM(VOLUME_CG) PLAN_RKAB from plan_production_daily pp
                left join master_bisnis_unit bu on bu.active=true and pp.iup=bu.name 
                where category='RKAB'
                GROUP BY bu.code
            )plan_rkab on plan_rkab.iup=data.bisnis_unit
            group by data.bisnis_unit,plan_rkab.plan_rkab
        """
        return query


class QeuryInventoryUpdateMiners(BcrQeuryInventoryUpdate):

    def QueryIUSubActivity(self, bu_id):
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = '''
            select
            inv.inv,
            sum(inv.stock_update) stock_volume,
            max(inv.date_update) last_update
            from inventory_resume inv
            left join master_bisnis_unit bu on bu.code=inv.iup
            left join master_sub_activity msa on msa.name=inv.inv
            where bu.bu_company_id in('%s')
            group by inv.inv
        ''' % (bu_id)
        return query

    def QueryIUIUP(self, bu_id):
        bu_id = "','".join([str(elem) for elem in bu_id])
        query = '''
            select
            inv.inv,
            inv.iup,
            sum(inv.stock_update) stock_volume,
            max(inv.date_update) last_update
            from inventory_resume inv
            left join master_bisnis_unit bu on bu.code=inv.iup
            left join master_sub_activity msa on msa.name=inv.inv
            where bu.bu_company_id in('%s')
            group by inv.inv,inv.iup
        ''' % (bu_id)
        return query

    def QueryIUSeam(self, bu_id, sub_activity):
        bu_id = "','".join([str(elem) for elem in bu_id])
        sub_activity = "','".join([str(elem) for elem in sub_activity])
        query = '''
            select inv.inv,
            inv.iup,
            inv.source,
            sum(inv.stock_update) stock_volume,
            max(inv.date_update) last_update
            from inventory_resume inv
            left join master_bisnis_unit bu on bu.code=inv.iup
            left join master_sub_activity msa on msa.name=inv.inv
            where bu.bu_company_id in('%s')
            and msa.id in ('%s')
            group by inv.inv,inv.iup,inv.source
        ''' % (bu_id, sub_activity)
        return query
