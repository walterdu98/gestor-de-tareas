from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from .forms import LoginForm
from .models import User, Role, userRole, SupervisorEmpleado 
from tasks.models import Task


def obtener_permiso_maximo(user):
    """Calcula el nivel de permiso del usuario actual"""
    if user.is_superuser:
        return 6 
    roles_usuario = userRole.objects.filter(user=user)
    return max([ur.role.modificar_usuarios for ur in roles_usuario], default=0)



def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard') 
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('core:dashboard') 
            else:
                messages.error(request, 'Usuario o contraseña inválidos.')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('users:login') 



@login_required
def user_management_view(request):
    permiso = obtener_permiso_maximo(request.user)
    
    if permiso < 5:
        raise PermissionDenied

    usuarios = User.objects.annotate(
        empleados_asignados_count=Count('empleados_asignados', distinct=True), 
        tareas_realizadas=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado='FINALIZADA'), distinct=True),
        tareas_pendientes=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado__in=['PENDIENTE','PENDIENTE_REVISION']), distinct=True),
        tareas_no_realizadas=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado='NO_COMPLETADA'), distinct=True),
    ).order_by('user_id')

    supervisores = User.objects.filter(user_roles__role__role_name='Supervisor')
    todos_los_roles = Role.objects.all()

    context = {
        'usuarios': usuarios,
        'supervisores': supervisores,
        'roles': todos_los_roles,
        'es_admin': request.user.is_superuser,
        'max_perm': permiso,
    }

    return render(request, 'users/user_list.html', context)

@login_required
def save_user_action(request, user_id=None):
    """Maneja la creación/edición. Solo accesible para permiso >= 5"""
    permiso = obtener_permiso_maximo(request.user)
    
    if permiso < 5:
        raise PermissionDenied

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role_id = request.POST.get('role')
        supervisor_id = request.POST.get('supervisor')

        try:
            if user_id:  
                target = get_object_or_404(User, user_id=user_id)
                es_admin = request.user.is_superuser

                if target != request.user:
                    if permiso == 6 and not es_admin and target.is_superuser:
                        raise ValueError("Como Jefe no puedes editar al Administrador.")
                    if es_admin and obtener_permiso_maximo(target) == 6:
                        raise ValueError("Como Admin no puedes editar al Jefe.")

                target.username = username

                if password and password.strip() != "":
                    target.set_password(password)
                    target.save()
                    if request.user == target:
                        update_session_auth_hash(request, target)
                else:
                    target.save()

                if role_id:
                    userRole.objects.update_or_create(
                        user=target,
                        defaults={'role_id': role_id}
                    )

                if supervisor_id:
                    SupervisorEmpleado.objects.update_or_create( 
                        empleado=target, 
                        defaults={'supervisor_id': supervisor_id}
                    )
                else:
                    SupervisorEmpleado.objects.filter(empleado=target).delete() 

                messages.success(request, f"✏️ Usuario '{username}' actualizado correctamente.")

            else:  
                if not username or not password:
                    raise ValueError("Debes ingresar usuario y contraseña.")

                target = User.objects.create_user(
                    username=username,
                    password=password
                )

                if role_id:
                    userRole.objects.create(user=target, role_id=role_id)

                if supervisor_id:
                    SupervisorEmpleado.objects.create( 
                        empleado=target, 
                        supervisor_id=supervisor_id
                    )

                messages.success(request, f"✅ Usuario '{username}' creado correctamente.")

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error inesperado: {str(e)}")

    return redirect('users:user_management')