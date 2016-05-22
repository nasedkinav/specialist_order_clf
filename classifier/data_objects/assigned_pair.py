import numpy as np

from django.db import connections

from classifier.data_objects import *
from classifier.data_objects.order import Order
from classifier.data_objects.specialist import Specialist
from classifier.utils.transform import *

LEVEL_DELTA = 5
EXPERIENCE_DELTA = 5


class AssignedPair:
    def __init__(self, order, specialist):
        self.order = order
        self.specialist = specialist

        self.success = int(self.order.success if self.specialist.id == self.order.last_specialist else False)

        # proceed specialist level and experience match
        if self.specialist.data['s_level_set'] and self.order.data['o_level_set']:
            level_distance = {'set': 1, 'distance': float(int(self.specialist.level) - int(self.order.level)) / LEVEL_DELTA}
        else:
            level_distance = {'set': 0, 'distance': 0}

        if self.specialist.data['s_experience_set'] and self.order.data['o_experience_set']:
            experience_distance = {'set': 1, 'distance': float(int(self.specialist.experience) - int(self.order.experience)) / EXPERIENCE_DELTA}
        else:
            experience_distance = {'set': 0, 'distance': 0}

        # proceed matched service
        service_match = set()
        if len(self.order.service):
            service_match = self.order.service.intersection(set(self.specialist.service.keys()))

        # proceed price difference
        price_defined = 0
        price_distance = .0
        if len(service_match) and self.order.data['o_price_per_hour']:
            price_defined = 1
            price_distance = self.specialist.service[service_match.pop()] - self.order.data['o_price_per_hour']

        self.data = {
            'ap_gender_match': to_binary(self.gender_match()),
            'ap_location_match': to_binary(self.location_match()),

            # level distance
            'ap_level_distance_set': level_distance['set'],
            'ap_level_distance_difference': level_distance['distance'],

            # experience distance
            'ap_experience_distance_set': experience_distance['set'],
            'ap_experience_distance_difference': experience_distance['distance'],

            'ap_matched_services': len(service_match),

            'ap_price_defined': price_defined,
            'ap_price_distance': price_distance,

            'ap_specialist_in_chosen': to_binary(self.specialist.id in self.order.chosen_specialists),
            'ap_specialist_in_replied': to_binary(self.specialist.id in self.order.chosen_specialists)
        }

        for d in [self.order.data, self.specialist.data]:
            self.data.update(d)

    def gender_match(self):
        if self.order.data['o_allow_man'] and self.order.data['o_allow_woman']:
            return True
        if self.order.data['o_allow_man'] and self.specialist.data['s_gender']:
            return True
        if self.order.data['o_allow_woman'] and not self.specialist.data['s_gender']:
            return True
        return False

    def location_match(self):
        if self.order.data['o_place_client'] and self.order.data['o_place_specialist'] and self.order.data['o_place_remote']:
            # indifferent
            return True
        if self.order.data['o_place_client']:
            if len(self.order.region.intersection(self.specialist.out_region)) or \
                            'all' in self.specialist.out_region or \
                            'ttl' in self.specialist.out_region:
                return True
            else:
                return False
        if self.order.data['o_place_specialist']:
            if len(self.order.region.intersection(self.specialist.self_region)) or \
                    len(self.order.station.intersection(self.specialist.self_station)):
                return True
            else:
                return False
        if self.order.data['o_place_remote'] and self.specialist.data['s_remote']:
            return True

        return False

    def transform(self):
        K = sorted(self.data)
        X = [self.data[k] for k in K]

        return K, np.array(X), self.success

    @staticmethod
    def collect_objects(start_dt, end_dt):
        K, X, y = None, [], []

        cursor = connections['classifier'].cursor()
        cursor.execute("""
            select
                id
            from
                ri_orders
            where
                receivd between '%s' and '%s'
        """ % (start_dt, end_dt))
        for o_row in dict_fetchall(cursor):
            cursor.execute("""
                select
                    prep_id
                from
                    ri_events
                where
                    order_id = %s
                    and ev_code = 'p_nazn'
            """ % o_row['id'])
            order = Order(o_row['id'])
            for s_row in dict_fetchall(cursor):
                K, ap_X, ap_y = AssignedPair(order, Specialist(s_row['prep_id'])).transform()
                X.append(ap_X)
                y.append(ap_y)

        # close connection
        cursor.close()
        return K, X, y
