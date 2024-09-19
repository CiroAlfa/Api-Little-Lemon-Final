from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MenuItemViewSet, CartViewSet, OrderViewSet, OrderItemViewSet, UserGroupViewSet, CustomObtainAuthToken, UserViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'menuitems', MenuItemViewSet)
router.register(r'menu-items', MenuItemViewSet)
router.register(r'users', UserViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'cart', CartViewSet)
router.register(r'orderitems', OrderItemViewSet)
router.register(r'user-group', UserGroupViewSet, basename='user-group')
router.register(r'menu-items', MenuItemViewSet, basename='unique-menuitem')


urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', CustomObtainAuthToken.as_view(), name='api_token_auth'),
]