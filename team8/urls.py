from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    # Catch-all under /team8/ (prefix added by core urls)
    re_path(r"^(?P<path>.*)$", csrf_exempt(views.gateway_proxy), name="team8-proxy"),
]
