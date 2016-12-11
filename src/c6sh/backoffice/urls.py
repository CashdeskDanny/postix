from django.conf.urls import url

from . import views

urlpatterns = [
    url('^login/$', views.LoginView.as_view(), name='login'),
    url('^logout/$', views.logout_view, name='logout'),
    url('^switch-user/$', views.switch_user, name='switch-user'),

    url('^create_user/$', views.create_user_view, name='create-user'),

    url('^session/new/$', views.new_session, name='new-session'),
    url('^session/(?P<pk>[0-9]+)/end/$', views.end_session, name='end-session'),
    url('^session/(?P<pk>[0-9]+)/report/$', views.session_report, name='session-report'),
    url('^session/(?P<pk>[0-9]+)/resupply/$', views.resupply_session, name='resupply-session'),
    url('^session/(?P<pk>[0-9]+)/$', views.SessionDetailView.as_view(), name='session-detail'),
    url('^session/$', views.SessionListView.as_view(), name='session-list'),
    url('^reports/$', views.ReportListView.as_view(), name='report-list'),

    url('^wizard/$', views.WizardSettingsView.as_view(), name='wizard-settings'),

    url('^$', views.MainView.as_view(), name='main'),
]
