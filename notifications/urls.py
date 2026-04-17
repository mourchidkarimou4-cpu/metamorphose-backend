from django.urls import path
from . import views

urlpatterns = [
    # ── Notifications admin ──────────────────────────────
    path('admin/notifications/',           views.liste_notifications),
    path('admin/notifications/lu/',        views.marquer_lu),
    path('admin/notifications/<int:pk>/lu/', views.marquer_lu),

    # ── Messagerie ───────────────────────────────────────
    path('admin/conversations/',           views.liste_conversations),
    path('messages/',                      views.messages_conversation),           # membre → sa conv
    path('messages/<int:membre_id>/',      views.messages_conversation),           # admin → conv d'un membre

    # ── Vagues ───────────────────────────────────────────
    path('admin/vagues/',                  views.vagues_list),
    path('admin/vagues/<int:pk>/',         views.vague_detail),
    path('admin/vagues/<int:pk>/membres/', views.ajouter_membre_vague),
    path('admin/vagues/<int:pk>/membres/<int:membre_id>/', views.retirer_membre_vague),

    # ── Progression ──────────────────────────────────────
    path('progression/',                          views.ma_progression),
    path('admin/progression/',                    views.progression_admin),
    path('admin/progression/<int:membre_id>/',    views.update_progression),

    # ── Satisfaction ─────────────────────────────────────
    path('satisfaction/',                  views.mon_formulaire_satisfaction),
    path('admin/satisfactions/',           views.satisfactions_admin),
    path('admin/satisfaction/envoyer/',    views.envoyer_formulaire_satisfaction),

    # ── Agenda ───────────────────────────────────────────
    path('agenda/',                        views.agenda_sessions),
    path('agenda/<int:pk>/',               views.agenda_session_detail),
    path('agenda/<int:pk>/rappel/',        views.envoyer_rappel_session),
]
