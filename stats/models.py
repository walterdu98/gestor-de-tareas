from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def dashboard_stats(request):
    
    if not (request.user.is_superuser or request.user.username == "Jefe"):
        return redirect('core:dashboard')

    
    usuarios = User.objects.annotate(
        completas=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado='FINALIZADA')),
        pendientes=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado__in=['PENDIENTE', 'PENDIENTE_REVISION'])),
        no_realizadas=Count('tareas_asignadas', filter=Q(tareas_asignadas__estado='NO_COMPLETADA'))
    ).order_by('-completas') 

    
    total_completas = sum(u.completas for u in usuarios)
    total_pendientes = sum(u.pendientes for u in usuarios)
    total_no_realizadas = sum(u.no_realizadas for u in usuarios)

    context = {
        'usuarios': usuarios,
        'total_completas': total_completas,
        'total_pendientes': total_pendientes,
        'total_no_realizadas': total_no_realizadas,
    }
    
    return render(request, 'stats/stats_view.html', context)