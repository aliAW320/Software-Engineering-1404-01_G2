from django.urls import re_path
from . import views

urlpatterns = [
    # Catch-all under /team8/ (the prefix is already added by app404.urls)
    re_path(r"^(?P<path>.*)$", views.gateway_proxy, name="team8-proxy"),
]
