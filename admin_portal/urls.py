from django.urls import path
from .admin_api import ForecastView
from .views import CustomLoginView
urlpatterns = [
    #Authentication process
    path('forecast-product', ForecastView.as_view(), name='foreacast-product'),
    path('forecast-sales', ForecastView.as_view(), name='foreacast-sales'),
    path("login/", CustomLoginView.as_view(), name="login"),
]
