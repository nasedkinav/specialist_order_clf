import os
import logging
import django_redis

from django.core.management.base import BaseCommand
from django.conf import settings

from classifier.evaluation import evaluate_pca


class Command(BaseCommand):
    args = '<scale>'
    help = 'Evaluate data PCA variance ratio'

    def handle(self, scale=False, *args, **options):
        logger = logging.getLogger(__name__)

        cache = django_redis.get_cache('default')
        data = cache.get(settings.CACHE_KEY_K_X_Y_DATA)

        if not data:
            logger.error("Empty data in cache by key '%s'" % settings.CACHE_KEY_K_X_Y_DATA)
            return

        logger.info("PCA variance ratio: %s" %
                    evaluate_pca(data['X'], data['y'], os.path.join(settings.BASE_DIR, 'dump/report/pca.png'), scale))
