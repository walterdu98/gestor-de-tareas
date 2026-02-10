from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from tasks.models import Task

@login_required
def stats_view(request):

    from users.models import userRole
    
    es_admin = request.user.is_superuser
    roles_usuario = userRole.objects.filter(user=request.user)
    
   
    max_perm = max([ur.role.modificar_usuarios for ur in roles_usuario], default=0)


    if not es_admin and max_perm != 5:
        raise PermissionDenied

    from users.models import User

    q_supervisor = request.GET.get('supervisor')
    q_estado = request.GET.get('estado')
    q_tipo_usuario = request.GET.get('tipo_usuario') 
    
    tareas = Task.objects.all()
    
    if q_supervisor:
        tareas = tareas.filter(creada_por_id=q_supervisor)
    if q_estado:
        tareas = tareas.filter(estado=q_estado)

    total = tareas.count()
    completadas = tareas.filter(estado='FINALIZADA').count()
    pendientes = tareas.filter(Q(estado='PENDIENTE') | Q(estado='PENDIENTE_REVISION')).count()
    no_completadas = tareas.filter(estado='NO_COMPLETADA').count()

    stats_supervisores = Task.objects.values('creada_por__username').annotate(
        total=Count('id')
    ).order_by('-total')

    usuarios_stats = User.objects.annotate(
        t_completadas=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado='FINALIZADA')),
        t_pendientes=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado__in=['PENDIENTE', 'PENDIENTE_REVISION'])),
        t_no_completadas=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado='NO_COMPLETADA')),
        t_total=Count('tareas_asignadas')
    ).order_by('-t_total')

    
    es_supervisor_query = Q(user_roles__role__modificar_usuarios=6)
    
    if q_tipo_usuario == 'supervisor':
        usuarios_stats = usuarios_stats.filter(es_supervisor_query)
    elif q_tipo_usuario == 'empleado': 
        usuarios_stats = usuarios_stats.exclude(es_supervisor_query)

    supervisores = User.objects.filter(es_supervisor_query).distinct()

    context = {
        'total': total,
        'completadas': completadas,
        'pendientes': pendientes,
        'no_completadas': no_completadas,
        'stats_supervisores': stats_supervisores,
        'usuarios_stats': usuarios_stats,
        'supervisores': supervisores,
        'filtros': {
            'supervisor': q_supervisor,
            'estado': q_estado,
            'tipo_usuario': q_tipo_usuario
        }
    }

    return render(request, 'stats/stats_view.html', context)