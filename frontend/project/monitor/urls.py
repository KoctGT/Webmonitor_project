from django.contrib.auth.views import LoginView
from django.urls import path
from .views import (monitor_index,
                    ignore,
                    solve,
                    charts,
                    setdate,
                    get_cookie_view,
                    set_cookie_view,
                    set_session_view,
                    get_session_view,
                    logout_view,
)

app_name = 'monitor'
urlpatterns = [
    path('', monitor_index, name="index"),
    path('ignore/<int:id>', ignore, name='ignore'),
    path('solve/<int:id>', solve, name='solve'),
    path('charts', charts, name='charts'),
    path('setdate', setdate, name='setdate'),
    path('cookie/get/', get_cookie_view, name='cookie-get'),
    path('cookie/set/', set_cookie_view, name='cookie-set'),
    path('session/set/', set_session_view, name='session-set'),
    path('session/get/', get_session_view, name='session-get'),
    path(
        "login/",
        LoginView.as_view(
            template_name="monitor/login.html",
            redirect_authenticated_user=True,
        ),
        name="login"),
    path("logout/", logout_view, name="logout"),

]