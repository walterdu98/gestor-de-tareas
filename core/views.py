from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.db.models import Q
from users.models import userRole

@login_required
def dashboard_view(request):

    from tasks.models import Task 

    permissions = {
        'tareas_empleados': 0, 
        'tareas_supervisor': 0,
        'estadisticas': 0,
        'modificar_usuarios': 0,
    }

    if request.user.is_superuser:
        permissions.update({
            'tareas_empleados': 2,
            'tareas_supervisor': 2,
            'estadisticas': 4,
            'modificar_usuarios': 5,
        })
        roles_list = ['Superuser']
        max_perm = 5
    else:
        user_roles = userRole.objects.select_related('role').filter(user=request.user)
        roles_list = [ur.role.role_name for ur in user_roles]
        max_perm = 0

        for ur in user_roles:
            r = ur.role
            permissions['tareas_empleados'] = max(permissions['tareas_empleados'], r.tareas_empleados)
            permissions['tareas_supervisor'] = max(permissions['tareas_supervisor'], r.tareas_supervisor)
            permissions['estadisticas'] = max(permissions['estadisticas'], r.estadisticas)
            
            m_user = r.modificar_usuarios
            permissions['modificar_usuarios'] = max(permissions['modificar_usuarios'], m_user)
            if m_user > max_perm: 
                max_perm = m_user

    
    base_qs = Task.objects.all()

    if request.user.is_superuser or max_perm == 5:
        tareas_qs = base_qs.filter(Q(creada_por=request.user) | Q(creada_por__is_superuser=True)).distinct()
    elif max_perm == 6:
        tareas_qs = base_qs.filter(Q(creada_por=request.user) | Q(asignado_a=request.user)).distinct()
    else:
        tareas_qs = base_qs.filter(asignado_a=request.user)

    tareas_recientes = tareas_qs.order_by('-id')[:8]

    context = {
        'user': request.user,
        'roles': roles_list,
        'permissions': permissions,
        'tareas_recientes': tareas_recientes,
        'max_perm': max_perm,
    }
    return render(request, 'core/dashboard.html', context)