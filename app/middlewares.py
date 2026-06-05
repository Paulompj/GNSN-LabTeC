# middlewares.py
from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
                request.user.is_authenticated
                and getattr(request.user, "trocar_senha", False)
                and request.path not in [reverse("app:password_change"), reverse("app:logout")]
        ):
            return redirect("app:password_change")
        return self.get_response(request)
