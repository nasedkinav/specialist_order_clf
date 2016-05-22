import logging
import django_redis

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings

from classifier.data_objects.assigned_pair import AssignedPair


class Command(BaseCommand):
    args = '<start_dt> <end_dt> <cache_data>'
    help = 'Collect classifier data'

    def handle(self, start_dt, end_dt, cache_data=False, *args, **options):
        assert start_dt <= end_dt, "Start datetime cannot be greater than end datetime"
        logger = logging.getLogger(__name__)

        logger.info("Start collecting classifier data between (%s) and (%s)" % (start_dt, end_dt))
        logger.info("Cache: %s" % "enabled" if cache_data else "disabled")

        try:
            keys, X, y = AssignedPair.collect_objects(start_dt, end_dt)
        except Exception as e:
            logger.error("Error occurred while collecting classifier data: '%s'" % e.message)
            return

        logger.info("Classifier data processed. Collected %s objects" % len(X))
        if cache_data:
            cache = django_redis.get_cache('default')
            cache.set(key=settings.CACHE_KEY_K_X_Y_DATA, value={'K': keys, 'X': X, 'y': y}, timeout=settings.CACHE_TIME['1_month'])
            logger.info("Classifier data cached in %s" % settings.CACHE_TIME['1_month'])

        logger.info("Data collection ended")

        # data evaluation
        call_command('evaluate_metrics')
        call_command('evaluate_pca')
