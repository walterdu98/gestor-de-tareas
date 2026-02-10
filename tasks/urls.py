from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='tasks_list'),
    path('crear/', views.task_create, name='task_create'),
    path('editar/<int:task_id>/', views.task_edit, name='task_edit'),
    path('finalizar/<int:task_id>/', views.task_finish, name='task_finish'),
    path('cambiar-estado/<int:task_id>/', views.task_change_status, name='task_change_status'),
    path('eliminar/<int:task_id>/', views.task_delete, name='task_delete'),
    path('notificacion/leer/<int:notif_id>/', views.marcar_notificacion_leida, name='marcar_leida'),
]