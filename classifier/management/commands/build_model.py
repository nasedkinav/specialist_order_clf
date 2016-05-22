import time
import logging
import django_redis

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings

from classifier.clf import Classifier, CLF_POOL, SCALER_POOL
from classifier.evaluation import evaluate_model


class Command(BaseCommand):
    args = '<start_dt> <end_dt>'
    help = 'Build classifier model'

    def handle(self, start_dt, end_dt, *args, **options):
        assert start_dt <= end_dt, "Start datetime cannot be greater than end datetime"
        logger = logging.getLogger(__name__)

        logger.info("Start build of classifier model for dates between (%s) and (%s)" % (start_dt, end_dt))

        cache = django_redis.get_cache('default')
        data = cache.get(settings.CACHE_KEY_K_X_Y_DATA)
        if not data:
            logger.info("No objects in cache. Start collection")
            call_command('collect_data', (start_dt, end_dt, True))
            while True:
                time.sleep(60)
                data = cache.get(settings.CACHE_KEY_K_X_Y_DATA)
                if data:
                    break

        logger.info("Start model estimation and evaluation")
        best_clf = None
        best_clf_str = None
        best_val = None
        best_params = None

        keys, X, y = data['K'], data['X'], data['y']
        for selector in [False, True]:
            for scaler in [SCALER_POOL['min_max'], SCALER_POOL['standart']]:
                # for clf in CLF_POOL.values():
                for clf in [CLF_POOL['naive_bayes'], CLF_POOL['logistic_regression'], CLF_POOL['sgd_logistic_regression'], CLF_POOL['sgd_svm']]:
                    if isinstance(scaler, type(SCALER_POOL['standart'])) and isinstance(clf, type(CLF_POOL['naive_bayes'])):
                        # multinomial naive bayes does not accept negative input data
                        continue
                    model = Classifier(clf, scaler, selector)
                    # score, true_0, true_1 = evaluate_model(model, X, y, 2)
                    score, true_0, true_1 = evaluate_model(model, X, y)
                    if not best_val or best_val < true_0:
                        # maximize percentage of true "failed" predictions
                        best_val = true_0
                        best_clf = model
                        best_clf_str = model.__str__()
                        best_params = {'score': score, 'true_failed': true_0, 'true_closed': true_1}

        # train best model
        best_clf.fit(X, y)

        logger.info("\nBest model:\n%s\nScore: %s\nTrue_failed: %s\nTrue_closed: %s" % (best_clf_str, best_params['score'], best_params['true_failed'], best_params['true_closed']))
        cache.set(key=settings.CACHE_KEY_MODEL, value=best_clf, timeout=settings.CACHE_TIME['1_month'])
        logger.info("Classifier model created and cached")
