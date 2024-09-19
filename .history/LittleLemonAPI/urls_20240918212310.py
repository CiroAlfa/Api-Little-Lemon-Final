from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MenuItemViewSet, CartViewSet, OrderViewSet, OrderItemViewSet, CustomObtainAuthToken
from . import views

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'menuitems', MenuItemViewSet)
router.register(r'cart', CartViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'orderitems', OrderItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', CustomObtainAuthToken.as_view(), name='api_token_auth'),
    path('groups/users/add/', views.assign_user_to_group, name='assign_user_to_group'),
    path('categories/add/', views.add_category, name='add_category'),
    path('menu-items/add/', views.add_menu_item, name='add_menu_item'),
]