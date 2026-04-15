from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages

def group_required(*group_names):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)

            # Adiciona a mensagem de erro
            messages.warning(request, "Você não tem permissão para acessar esta página.")

            # Renderiza a página de acesso negado mantendo o layout do site
            return render(request, 'index.html')

        return _wrapped_view
    return decorator
