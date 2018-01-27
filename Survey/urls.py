from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Standard pages
    url(r'^info/$', views.info, name='info'),
    #url(r'^home/$', views.index, name='home'),
    #url(r'^$', auth_views.login, name='index'),
    #Password
    url(r'^password/$', views.change_password, name='change_password'),
    # User pages
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^profile/$', views.CurrentCustomUserDetailView.as_view(), name='profile'),  # Utente corrente
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^profile/edit$', views.UpdateProfileView.as_view(), name='edit_profile'),  # Utente corrente
    # Survey pages
    url(r'^$', views.survey, name='survey'),
    url(r'^survey/$', views.survey, name='survey'),
    url(r'^survey_questions/$' , views.survey_questions, name='survey_questions'),
    url(r'^question/(?P<survey_id>[0-9]+)/(?P<topic_id>[0-9]+)/(?P<question_id>[0-9]+)/$', views.question, name='question'),
    url(r'^vote/(?P<question_id>[0-9]+)/$', views.vote, name='vote'),
    url(r'^report/(?P<survey_id>[0-9]+)/$', views.report, name='report'),
    url(r'^skip/(?P<survey_id>[0-9]+)/$', views.skip, name='skip'),
    # Development
    url(r'^users/$', views.CustomUserListView.as_view(), name='users'),                                                 # Utenti
    # url(r'^user/(?P<id_card>\d+)$', views.CustomUserDetailView.as_view(), name='user_detail'),                        # Utente
]