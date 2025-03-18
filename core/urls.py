from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pricing/', views.pricing, name='pricing'),
    path('faq/', views.faq, name='faq'),
    path('support/', views.support, name='support'),
    path('how-it-works/', views.how_it_works, name='how-it-works'),
    path('login/', views.Auth0LoginView.as_view(), name='login'),
    path('signup/', views.Auth0SignupView.as_view(), name='signup'),
    path('callback/', views.Auth0CallbackView.as_view(), name='auth0_callback'),
    path('upload/', views.UploadImageView.as_view(), name='upload'),
] 