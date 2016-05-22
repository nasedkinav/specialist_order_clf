import classifier.views

from django.conf.urls import *

urlpatterns = [
    url('^api/predict$', classifier.views.predict_order, name='predict_order'),
    url('^api/model', classifier.views.model, name='model')
]
