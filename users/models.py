from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)

    USERNAME_FIELD = 'username'

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def get_role_name(self):
        role_rel = self.user_roles.first()
        return role_rel.role.role_name if role_rel else "Sin Rol"

class Role(models.Model):
    PERMISSION_CHOICES = [
        (0, 'No access'),
        (1, 'View only'),
        (2, 'Can create and modify all tasks and status'),
        (3, 'Can modify just status tasks (Employees)'),
        (4, 'Stadistics access'),
        (5, 'Boss can create and modify Employees and supervisors'), 
        (6, 'Supervisor can create and modify employees only'),     
        (7, 'Supervisor as employee (Only modify status)'),
    ]
    role_name = models.CharField(max_length=50, unique=True)
    
    tareas_empleados = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    tareas_supervisor = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    
    estadisticas = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    modificar_usuarios = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    

    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.role_name    

class userRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_roles'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'    
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.role_name}"    

class SupervisorEmpleado(models.Model):
    supervisor = models.ForeignKey(User, related_name='empleados_asignados', on_delete=models.CASCADE)
    empleado = models.OneToOneField(User, related_name='supervisor_asignado', on_delete=models.CASCADE)

    class Meta:
        db_table = 'supervisor_empleado'
        verbose_name = 'Supervisor - Empleado'
        verbose_name_plural = 'Supervisor - Empleados'
        
    def __str__(self):
        return f"{self.supervisor.username} → {self.empleado.username}"