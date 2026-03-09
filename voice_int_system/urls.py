from django.contrib import admin
from django.urls import path, include
from accounts.views import home
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('internal/', include('internal_check.urls')),
    path('search_yt/', include('search_yt.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)