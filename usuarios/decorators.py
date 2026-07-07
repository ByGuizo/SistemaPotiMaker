from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def coordenador_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_coordenador:
            raise PermissionDenied('Apenas coordenadores podem executar esta ação.')
        return view_func(request, *args, **kwargs)
    return _wrapped
