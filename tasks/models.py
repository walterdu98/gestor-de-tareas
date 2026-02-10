from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse

class Task(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PENDIENTE_REVISION', 'Pendiente de revisión'),
        ('FINALIZADA', 'Finalizada'),
        ('NO_COMPLETADA', 'No Completada'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    asignado_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tareas_asignadas')
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tareas_creadas')
    creada_en = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField(null=True, blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)

    aprobada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='tareas_aprobadas'
    )
    
    reabierta = models.BooleanField(default=False)
    asignado_original = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='tareas_reabiertas_previas'
    )

    class Meta:
        db_table = 'tasks'
        ordering = ['-creada_en']

    def __str__(self):
        return self.titulo or f"Tarea {self.id}"

    @property
    def esta_vencida(self):
        """Devuelve True si la tarea pasó su fecha límite y no está finalizada"""
        if self.fecha_limite and self.estado != 'FINALIZADA':
            return timezone.now() > self.fecha_limite   
        return False

    def get_filter_url(self):
        """Genera la URL para ver esta tarea filtrada en el Panel de Tareas"""
        return f"{reverse('tasks:tasks_list')}?nombre={self.id}"

    def save(self, *args, **kwargs):
        if self.estado in ['FINALIZADA', 'NO_COMPLETADA']:
            if not self.fecha_finalizacion:
                self.fecha_finalizacion = timezone.now()
        else:
            self.fecha_finalizacion = None
            
        super().save(*args, **kwargs)

class Notificacion(models.Model):
    receptor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notificaciones'
    )
    tarea = models.ForeignKey('Task', on_delete=models.CASCADE)
    mensaje = models.CharField(max_length=255)
    # Almacena el link con el parámetro ?nombre=ID
    link = models.CharField(max_length=255, null=True, blank=True) 
    leido = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificaciones'
        ordering = ['-creada_en']

    def __str__(self):
        return f"Notificación #{self.id} para {self.receptor.username}"