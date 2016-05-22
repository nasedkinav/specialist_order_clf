import logging
import django_redis

from django.core.management.base import BaseCommand
from django.conf import settings

from classifier.evaluation import evaluate_data


class Command(BaseCommand):
    args = ''
    help = 'Evaluate data metrics weights'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

        cache = django_redis.get_cache('default')
        data = cache.get(settings.CACHE_KEY_K_X_Y_DATA)

        if not data:
            logger.error("Empty data in cache by key '%s'" % settings.CACHE_KEY_K_X_Y_DATA)
            return

        logger.info("Metrics report")
        logger.info('\n' + '\n'.join('{0}: {1:.4f}'.format(k, v) for k, v in evaluate_data(data['K'], data['X'], data['y'])))
