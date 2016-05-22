from django.db import connections

from classifier.data_objects import dict_fetchall
from classifier.data_objects.order import SPECIALIST_LEVEL_ENUM, SPECIALIST_EXPERIENCE_ENUM
from classifier.utils.transform import *


class Specialist:
    def __init__(self, _id):
        self.id = _id

        cursor = connections['classifier'].cursor()
        cursor.execute("select * from ri_preps where id = '%s'" % self.id)
        fetchall = dict_fetchall(cursor)
        if not fetchall:
            raise Exception("Undefined specialist '%s'" % self.id)
        row = fetchall[0]

        self.self_region = set()
        self.self_station = set()
        self.out_region = set()

        cursor.execute("""
            select
                typ,
                key_id
            from
                ri_datap
            where
                prep_id = '%s'
                and typ in ('mm', 'mc', 'rgn')
        """ % self.id)
        for res in dict_fetchall(cursor):
            if res['typ'] == 'mm':
                self.self_station.add(res['key_id'])
            elif res['typ'] == 'mc':
                self.self_region.add(res['key_id'])
            elif res['typ'] == 'rgn':
                self.out_region.add(res['key_id'])

        # service prices
        self.service = {}
        cursor.execute("""
            select
                pservice_id,
                price
            from
                ri_pprices
            where
                prep_id = '%s'
        """ % self.id)
        for res in dict_fetchall(cursor):
            if res['price']:
                self.service[int(res['pservice_id'])] = float(res['price'])

        photo_quality_set = to_binary(row['pqual'] >= -200 and row['pqual'] != 0)

        self.data = {
            's_gender': to_binary(row['gender'] == 'm'),  # 1 for man, 0 for woman

            # photo data
            's_photo_set': not_empty_str(row['photo']),
            's_photo_quality_set': photo_quality_set,
            's_photo_quality': row['pqual'] if photo_quality_set else 0,

            's_wage': not_empty_str(row['stavka']),
            's_remote': to_binary(row['web']),
            's_requirements_set': not_empty_str(row['req']),

            # test data
            's_test_passed': to_binary(row['teste'] != 0),
            's_test_value': row['teste'],
            's_profile_formed': to_binary(row['oform']),
            's_profile_value': row['oform'],

            's_vip': row['vip'],
            's_youtube': not_empty_str(row['youtube']),
            's_skype': not_empty_str(row['skype']),

            # reviews data
            's_review_count': 0,
            's_review_mean': 0,

            # level and experience data
            's_level_set': to_binary(15 <= row['st_sci'] <= 35),
            's_experience_set': to_binary(50 <= row['st_edu'] <= 85),

            # professionality data
            's_professionality': float(row['pfz100']),
            's_rank': float(row['rank5']),
            's_satiety': float(row['satiety']),
            's_discipline': float(row['disciplina']),

            # location and service data
            's_service_count': len(self.service.keys()),
            's_self_region_count': len(self.self_region),
            's_self_station_count': len(self.self_station),
            's_out_region_count': len(self.out_region)
        }

        # reviews data
        cursor.execute("""
            select
                count(*) as cnt,
                10 - avg(mark) as mean
            from
                ri_reviews
            where
                prep_id = '%s'
                and mark != '-1'
            group by prep_id
        """ % self.id)
        for res in dict_fetchall(cursor):
            self.data['s_review_count'] = float(res['cnt'])
            self.data['s_review_mean'] = float(res['mean'])

        self.level = row['st_sci']
        self.experience = row['st_edu']

        level = one_hot_encode(self.level, SPECIALIST_LEVEL_ENUM, 's_level_')
        experience = one_hot_encode(self.experience, SPECIALIST_EXPERIENCE_ENUM, 's_experience_')

        for d in [level, experience]:
            self.data.update(d)

        # close connection
        cursor.close()
