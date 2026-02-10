from django.urls import path
from . import views

app_name = 'users' 
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('gestion/', views.user_management_view, name='user_management'),
    path('save/', views.save_user_action, name='create_user'),
    path('save/<str:user_id>/', views.save_user_action, name='edit_user_action'),
]