import time

from datetime import datetime

from django.db import connections

from classifier.data_objects import dict_fetchall
from classifier.utils.transform import *

COURSE_DICT = {
    -40: {'set': 1, 'short': 0, 'long': 4},  # long
    -30: {'set': 1, 'short': 0, 'long': 3},  # full
    -20: {'set': 1, 'short': 0, 'long': 2},  # limited
    -10: {'set': 1, 'short': 0, 'long': 1},  # express
    0: {'set': 0, 'short': 0, 'long': 0},  # not set
    1: {'set': 1, 'short': 1, 'long': 0},  # 1 time
    2: {'set': 1, 'short': 2, 'long': 0},  # 2 times
    3: {'set': 1, 'short': 3, 'long': 0},  # 3 times
    4: {'set': 1, 'short': 4, 'long': 0},  # 4 times
}
COURSE_LONG_ENUM = {
    1: 'express',
    2: 'limited',
    3: 'full',
    4: 'long'
}

PLACE_DICT = {
    0:  {'client': 1, 'specialist': 1, 'remote': 1},  # any location
    -1: {'client': 0, 'specialist': 1, 'remote': 0},  # specialist
    1:  {'client': 1, 'specialist': 0, 'remote': 0},  # client
    3:  {'client': 0, 'specialist': 0, 'remote': 1},  # remotely
}

COURSE_LENGTH_DICT = {  # length in days period
    6: 28,  # ASSUMPTION: several times classes, supposed to be done in 4 weeks
    5: 7,   # ASSUMPTION: one-time class, supposed to be done in one week
    4: 30,
    3: 45,
    2: 60,
    1: 90,
    0: 120,
    -1: 180,
    -2: 240,
}

COURSE_AIM_ENUM = {
    -30: 'self',
    -20: 'life',
    -10: 'work',
    10: 'increase_second',
    20: 'olympic',
    30: 'increase',
    40: 'important'
}

SPECIALIST_LEVEL_ENUM = {
    15: 'student',
    20: 'graduate',
    25: 'candidate',
    30: 'phd',
    35: 'native'
}

SPECIALIST_EXPERIENCE_ENUM = {
    50: 'little',
    55: 'middle',
    60: 'school',
    65: 'course',
    70: 'experienced',
    75: 'university',
    80: 'expert',
    85: 'professor'
}

SESSION_PLATFORM_DICT = {
    'o_session_platform_android': ['Android'],
    'o_session_platform_ios': ['iOS'],
    'o_session_platform_macos': ['MacOSX'],
    'o_session_platform_winphone': ['WinPhone7.5', 'WinPhone8', 'WinPhone8', 'WinRT8', 'WinRT8.1'],
    'o_session_platform_old_win': ['Win98', 'WinNT', 'WinVista', 'WinXP'],
    'o_session_platform_new_win': ['Win7', 'Win8', 'Win8.1'],
    'o_session_platform_linux': ['Linux', 'Ubuntu'],
    'o_session_platform_other': ['CellOS', 'ChromeOS', 'JAVA', 'RIM OS', 'SymbianOS', 'unknown'],
}


class Order:
    def __init__(self, _id):
        self.id = _id

        # retrieve order data
        cursor = connections['classifier'].cursor()
        cursor.execute('select * from ri_orders where id = %s' % self.id)
        row = dict_fetchall(cursor)[0]

        # gather params
        self.success = (40 <= row['status'] < 90) or (row['status'] >= 90 and row['sto'] in (10, 30))

        self.chosen_specialists = [] if not row['chosen'] else [spec for spec in row['chosen'].split('\n') if spec]
        self.replied_specialists = [] if not row['repl'] else [spec for spec in row['repl'].split('\n') if spec]

        self.last_specialist = row['prep']

        creation_date = row['receivd'].timetuple() if isinstance(row['receivd'], datetime) \
            else datetime.strptime(row['receivd'], '%Y-%m-%d %H:%M:%S').timetuple()

        place = PLACE_DICT.get(row['alloc'], PLACE_DICT[0])  # in case of undefined: any location
        course = COURSE_DICT.get(row['sz'], COURSE_DICT[0])  # in case of undefined: not set
        frequency = self.prepare_frequency(row['razvned'])

        self.data = {
            # received order date (daytime) [night, morning, afternoon, evening]
            'o_daytime': (creation_date.tm_hour * 60 + creation_date.tm_min) / 360,

            # pupil data
            'o_pupil_set': not_empty_str(row['pupil']),
            'o_pupil_email_set': not_empty_str(row['email']),
            'o_pupil_age_set': to_binary(row['uvozr']),
            'o_pupil_age': row['uvozr'],
            'o_pupil_level_set': to_binary(row['ulevel']),
            'o_pupil_level': row['ulevel'],

            # place data
            'o_place_client': place['client'],
            'o_place_specialist': place['specialist'],
            'o_place_remote': place['remote'],

            # chosen specialists count
            'o_specialists_chosen': len(self.chosen_specialists),
            'o_specialists_replied': len(self.replied_specialists),

            # gender requirements
            'o_allow_man': 0 if row['wgender'] == -2 else 1,
            'o_allow_woman': 0 if row['wgender'] == 2 else 1,

            # specialists experience and level requirements
            'o_level_set': to_binary(15 <= row['vzrst'] <= 35),
            'o_experience_set': to_binary(50 <= row['opyt'] <= 85),

            # course length requirements
            'o_course_length_set': course['set'],
            'o_course_length_short': course['short'],

            # course frequency in times per week
            'o_frequency_set': frequency['set'],
            'o_frequency_lower_bound': frequency['lower'],
            'o_frequency_upper_bound': frequency['upper'],

            # course length
            'o_course_day_length': COURSE_LENGTH_DICT.get(row['wlength'], 0),  # zero in case of undefined value

            # course aim
            'o_aim_set': to_binary(row['aimi'] != 0),

            # price data
            'o_price_order': clean_float(row['price']) or 0,
            'o_price_initial': clean_float(row['price0']) or 0,
            'o_price_per_hour': clean_float(row['wprice']) or 0,
            'o_price_total_class': clean_float(row['stoim']) or 0,

            # session data
            'o_session_set': 0,
            'o_session_length': 0,
            'o_session_num_views': 0,
            'o_session_visit_number': 0,

            # button value
            'o_button_clicked': 0,
            'o_button_mean': 0,
        }

        course_long = one_hot_encode(course['long'], COURSE_LONG_ENUM, 'o_course_long_')
        course_aim = one_hot_encode(row['aimi'], COURSE_AIM_ENUM, 'o_aim_')

        self.level = row['vzrst']
        self.experience = row['opyt']
        specialist_level = one_hot_encode(self.level, SPECIALIST_LEVEL_ENUM, 'o_level_')
        specialist_experience = one_hot_encode(self.experience, SPECIALIST_EXPERIENCE_ENUM, 'o_experience_')

        for d in [course_long, specialist_level, specialist_experience, course_aim]:
            self.data.update(d)

        # enrich session data
        self.data.update(dict(zip(SESSION_PLATFORM_DICT.keys(), [0] * len(SESSION_PLATFORM_DICT.keys()))))
        self.data['o_session_platform_other'] = 1

        cursor.execute("""select * from ri_sessions where order_id = %s""" % self.id)
        for res in dict_fetchall(cursor):
            self.data['o_session_set'] = 1
            self.data['o_session_length'] = time.mktime(res['last_hit'].timetuple()) - time.mktime(res['dt'].timetuple())
            self.data['o_session_num_views'] = res['num_views']
            self.data['o_session_visit_number'] = res['nb_viz_prj']
            for k, platforms in SESSION_PLATFORM_DICT.iteritems():
                if res['ua_os'] in platforms:
                    self.data['o_session_platform_other'] = 0
                    self.data[k] = 1
                    break

        # mean button value
        cursor.execute("""
            select
                count(*) as button_count,
                avg(key_id) as mean_val
            from
                ri_datao
            where
                order_id = {0}
                and typ = 'knpk'
                and key_id not like '%error%'
        """.format(self.id))
        for res in dict_fetchall(cursor):
            self.data['o_button_clicked'] = to_binary(res['button_count'])
            self.data['o_button_mean'] = res['mean_val'] if self.data['o_button_clicked'] else 0

        # region
        self.region = set()
        cursor.execute("""
            select
                key_id
            from
                ri_datao
            where
                order_id = %s
                and typ = 'mc'
        """ % self.id)
        for res in dict_fetchall(cursor):
            self.region.add(res['key_id'])

        # station
        self.station = set()
        cursor.execute("""
            select
                ri_datao.key_id,
                ri_mmetros.region_ids
            from
                ri_datao
                join ri_mmetros on ri_datao.key_id = ri_mmetros.id
            where
                ri_datao.order_id = %s
                and ri_datao.typ = 'mm'
        """ % self.id)
        for res in dict_fetchall(cursor):
            self.station.add(res['key_id'])
            self.region.update(set(res['region_ids'].split(',')))

        self.service = set()
        cursor.execute("""
            select
                key_id
            from
                ri_datao
            where
                order_id = %s
                and typ = 'vc'
        """ % self.id)
        for res in dict_fetchall(cursor):
            self.service.add(int(res['key_id']))

        # close connection
        cursor.close()

    @staticmethod
    def prepare_frequency(freq_val):
        if freq_val < 0:
            # -1 stands for 0.5 times per week
            # -2 stands for 0.25 times per week
            return {'set': 1, 'lower': -0.5 / freq_val, 'upper': -0.5 / freq_val}
        else:
            fs = str(freq_val)
            # one digit stands for times per week
            # two digits stand for lower and upper bound of times per week
            return {
                'set': to_binary(freq_val),
                'lower': float(fs[0]),
                'upper': float(fs[1] if len(fs) > 1 else fs[0])
            }
