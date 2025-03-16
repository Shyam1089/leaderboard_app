from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, WinnerViewSet, update_winners

app_name = 'api'

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'winners', WinnerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('update-winners/', update_winners, name='update-winners'),
]