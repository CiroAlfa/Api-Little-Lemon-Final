from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MenuItemViewSet, CartViewSet, OrderViewSet, OrderItemViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'menuitems', MenuItemViewSet)
router.register(r'cart', CartViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'orderitems', OrderItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]