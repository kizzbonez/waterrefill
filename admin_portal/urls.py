from django.urls import path
from .admin_api import ForecastView

urlpatterns = [
    #Authentication process
    path('forecast-product', ForecastView.as_view(), name='foreacast-product'),
    path('forecast-sales', ForecastView.as_view(), name='foreacast-sales'),

]
