from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'asignado_a', 'estado', 'creada_en')
    list_filter = ('estado', 'reabierta')
    search_fields = ('titulo', 'asignado_a__username')