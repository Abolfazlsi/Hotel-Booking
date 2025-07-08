from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import debug_toolbar
from django.views.generic import RedirectView
from django.urls import reverse_lazy


urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy("hotels:home"), permanent=False)),
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("hotels/", include("hotels.urls")),
    path('__debug__/', include(debug_toolbar.urls))

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
