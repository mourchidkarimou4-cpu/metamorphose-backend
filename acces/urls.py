from django.urls import path
from .views import VerifierCleView, ListeClesAdminView, GenererCleAdminView, ToggleCleAdminView

urlpatterns = [
    path('verifier/',              VerifierCleView.as_view()),
    path('admin/cles/',            ListeClesAdminView.as_view()),
    path('admin/generer/',         GenererCleAdminView.as_view()),
    path('admin/cles/<int:pk>/toggle/', ToggleCleAdminView.as_view()),
]
