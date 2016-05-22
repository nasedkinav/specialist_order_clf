import json
import logging
import django_redis
import numpy as np

from datetime import datetime, timedelta

from django.conf import settings
from django.http import JsonResponse, Http404, HttpResponseServerError
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt

from data_objects.order import Order
from data_objects.specialist import Specialist
from data_objects.assigned_pair import AssignedPair

from sklearn.pipeline import Pipeline


@csrf_exempt
def predict_order(request):
    logger = logging.getLogger(__name__)
    try:
        data = json.loads(request.body)
    except Exception as e:
        logger.error(e.message)
        return JsonResponse({'success': False, 'reason': e.message})

    if 'access_token' not in data or data['access_token'] != settings.ACCESS_TOKEN:
        return JsonResponse({'success': False, 'reason': 'Invalid access token'})

    cache = django_redis.get_cache('default')
    model = cache.get(settings.CACHE_KEY_MODEL)
    if not model:
        now = datetime.now()
        call_command('build_model', (str((now - timedelta(weeks=20)).date()), str(now.date())))

        return JsonResponse({'success': False, 'reason': 'Model is temporary unavailable. Retraining process started'})

    if 'order_id' not in data:
        return JsonResponse({'success': False, 'reason': 'Invalid order'})

    try:
        result = {}
        order = Order(int(data['order_id']))
        for s_id in set(data['specialists'] + order.chosen_specialists + order.replied_specialists):
            _, X, _ = AssignedPair(order, Specialist(s_id)).transform()
            result[s_id] = model.predict(np.array(X).reshape(1, -1))[0]

        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'success': False, 'reason': e.message})


@csrf_exempt
def model(request):
    logger = logging.getLogger(__name__)
    try:
        data = json.loads(request.body)
    except Exception as e:
        logger.error(e.message)
        return JsonResponse({'success': False, 'reason': e.message})

    if 'access_token' not in data or data['access_token'] != settings.ACCESS_TOKEN:
        return JsonResponse({'success': False, 'reason': 'Invalid access token'})

    cache = django_redis.get_cache('default')
    model = cache.get(settings.CACHE_KEY_MODEL)
    if not model:
        now = datetime.now()
        call_command('build_model', (str((now - timedelta(weeks=20)).date()), str(now.date())))

        return JsonResponse({'success': False, 'reason': 'Model is temporary unavailable. Retraining process started'})

    return JsonResponse({
        'success': True,
        'result': [str(v) for k, v in model.clf.steps] if isinstance(model.clf, Pipeline) else [str(model.clf)]
    })


def error404(request):
    return Http404()


def error500(request):
    return HttpResponseServerError()
