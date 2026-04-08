from django.contrib import admin
from django.urls import path, include, re_path
from administration import views as administration_views
from contenu.agentia_view import proxy_agent_ia
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/contenu/', include('contenu.urls')),
    path('api/liste-attente/', administration_views.inscrire_liste_attente),
    path('api/admin/', include('administration.urls')),
    path('api/cadeaux/', include('cadeaux.urls')),
    path('api/avis/', include('avis.urls')),
    path('api/paiement/', include('paiement.urls')),
    path('api/agent-ia/', proxy_agent_ia),
    # Media — fonctionne en dev ET en production
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
