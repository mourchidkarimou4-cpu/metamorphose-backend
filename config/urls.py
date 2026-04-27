from django.contrib import admin
from django.urls import path, include, re_path
from administration import views as administration_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from pathlib import Path
import mimetypes
import json

# ── Servir les fichiers statiques du build React ──────────────────
DIST = Path(settings.BASE_DIR) / 'frontend' / 'dist'

def serve_react(request, *args, **kwargs):
    index = DIST / 'index.html'
    if index.exists():
        return HttpResponse(index.read_text(), content_type='text/html')
    return HttpResponse('<h1>Frontend non buildé</h1>', status=200)

def serve_static_file(request, path):
    """Servir n'importe quel fichier statique depuis dist/"""
    file_path = (DIST / path).resolve()
    # Sécurité : interdire la sortie du dossier dist
    try:
        file_path.relative_to(DIST)
    except ValueError:
        return HttpResponse(status=403)
    if file_path.exists() and file_path.is_file():
        mime, _ = mimetypes.guess_type(str(file_path))
        return HttpResponse(file_path.read_bytes(), content_type=mime or 'application/octet-stream')
    return HttpResponse(status=404)

def serve_manifest(request):
    manifest = DIST / 'manifest.json'
    if manifest.exists():
        return HttpResponse(manifest.read_text(), content_type='application/manifest+json')
    data = {
        "name": "Méta'Morph'Ose",
        "short_name": "MetaMorphOse",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0A0A0A",
        "theme_color": "#C2185B",
        "icons": [
            {"src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    return HttpResponse(json.dumps(data), content_type='application/manifest+json')

urlpatterns = [
    path('api/live/', include('live.urls')),
    path('api/zoom/', include('zoom.urls')),
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
    path('api/aura/', include('aura.urls')),
    # Fichiers statiques React
    path('manifest.json', serve_manifest),
    re_path(r'^assets/(?P<path>.+)$', lambda req, path: serve_static_file(req, f'assets/{path}')),
    re_path(r'^icons/(?P<path>.+)$',  lambda req, path: serve_static_file(req, f'icons/{path}')),
    re_path(r'^sw\.js$',             lambda req: serve_static_file(req, 'sw.js')),
    # Catch-all React
    re_path(r'^(?!api/|admin/|static/|media/).*$', serve_react),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
