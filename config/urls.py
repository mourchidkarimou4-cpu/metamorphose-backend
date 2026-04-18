from django.contrib import admin
from django.urls import path, include, re_path
from administration import views as administration_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from pathlib import Path

urlpatterns = [
    path('api/live/', include('live.urls')),
    path('api/evenements/', include('evenements.urls')),
    path('api/communaute/', include('communaute.urls')),
    path('api/acces/', include('acces.urls')),
    path('api/masterclass/', include('masterclass.urls')),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/contenu/', include('contenu.urls')),
    path('api/liste-attente/', administration_views.inscrire_liste_attente),
    path('api/admin/', include('administration.urls')),
    path('api/cadeaux/', include('cadeaux.urls')),
    path('api/avis/', include('avis.urls')),
    path('api/paiement/', include('paiement.urls')),
    path('api/', include('notifications.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/tickets/', include('tickets.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ── Servir le frontend React (catch-all) ─────────────────────────
def serve_react(request, *args, **kwargs):
    index = Path(settings.BASE_DIR) / 'frontend' / 'dist' / 'index.html'
    if index.exists():
        return HttpResponse(index.read_text(), content_type='text/html')
    return HttpResponse('<h1>Frontend non buildé</h1><p>Lancez npm run build dans metamorphose-frontend</p>', status=200)

urlpatterns += [
    re_path(r'^(?!api/|admin/|static/|media/).*$', serve_react),
]
