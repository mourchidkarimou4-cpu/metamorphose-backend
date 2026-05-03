from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('evenements/',                  views.evenements_list),
    path('evenements/<slug:slug>/',      views.evenement_detail),
    path('reserver/',                    views.reserver),
    path('verifier/<uuid:code>/',        views.verifier_ticket),
    path('mes-tickets/',                 views.mes_tickets),
    # PIN scan
    path('verifier-pin/',                 views.verifier_pin),
    path('changer-pin/',                  views.changer_pin),
    # Admin scan
    path('scanner/<uuid:code>/',         views.scanner_ticket),
    # Admin CRUD
    path('admin/evenements/',            views.admin_evenements),
    path('admin/evenements/<int:pk>/',   views.admin_evenement_detail),
    path('admin/tickets/',               views.admin_tickets),
    path('admin/tickets/<int:pk>/',      views.admin_ticket_detail),
]
