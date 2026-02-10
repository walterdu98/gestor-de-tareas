from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, userRole, SupervisorEmpleado


class UserRoleInline(admin.TabularInline):
    model = userRole
    extra = 1
    max_num = 1

class SupervisorEmpleadoInline(admin.TabularInline): 
    model = SupervisorEmpleado
    fk_name = 'empleado' 
    extra = 1
    max_num = 1


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('user_id', 'username', 'get_role', 'is_staff', 'is_active')
    search_fields = ('user_id', 'username', 'email')
    ordering = ('-user_id',)
    inlines = [UserRoleInline, SupervisorEmpleadoInline] 
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    def get_role(self, obj):
        return obj.get_role_name
    get_role.short_description = 'Rol Actual'

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'tareas_empleados', 'tareas_supervisor', 'modificar_usuarios', 'estadisticas') 
    search_fields = ('role_name',)

    fieldsets = (
        (None, {'fields': ('role_name',)}),
        ('Niveles de Permisos (Tareas)', {
            'fields': (('tareas_empleados', 'tareas_supervisor'),), 
            'description': 'Niveles: 1=Ver, 2=Crear/Modificar, 3=Estado(Empleado), 7=Estado(Supervisor)' 
        }),
        ('Gestión y Reportes', {
            'fields': (('modificar_usuarios', 'estadisticas'),)
        }),
    )

@admin.register(userRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_user_id_num', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__user_id')

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Usuario'

    def get_user_id_num(self, obj):
        return obj.user.user_id
    get_user_id_num.short_description = 'ID Numérico'

@admin.register(SupervisorEmpleado) 
class SupervisorEmpleadoAdmin(admin.ModelAdmin): 
    list_display = ('supervisor', 'get_sup_id', 'empleado', 'get_emp_id') 
    list_select_related = ('supervisor', 'empleado')
    search_fields = ('supervisor__username', 'empleado__username', 'supervisor__user_id', 'empleado__user_id')
    
    def get_sup_id(self, obj):
        return obj.supervisor.user_id
    get_sup_id.short_description = 'ID Supervisor'

    def get_emp_id(self, obj): 
        return obj.empleado.user_id
    get_emp_id.short_description = 'ID Empleado'