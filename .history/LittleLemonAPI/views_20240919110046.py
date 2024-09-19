from datetime import timezone
from django.forms import ValidationError
from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth.models import User, Group

from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer, UserSerializer
from .permissions import IsManager, IsDeliveryCrew
from .permissions import IsManager


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsManager()]

    @action(detail=False, methods=['post'])
    def add(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['price']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['patch'], permission_classes=[IsManager])
    def set_item_of_the_day(self, request, pk=None):
        menu_item = self.get_object()
        menu_item.item_of_the_day = True
        MenuItem.objects.exclude(id=menu_item.id).update(item_of_the_day=False)
        menu_item.save()
        return Response({'status': 'item of the day set'})
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    @action(detail=True, methods=['post'])
    def assign_to_delivery_crew(self, request, pk=None):
        user = self.get_object()
        delivery_crew = Group.objects.get(name='Delivery Crew')
        user.groups.add(delivery_crew)
        return Response({'status': 'user assigned to delivery crew'})

class UserGroupViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'])
    def assign_user_to_group(self, request):
        username = request.data.get('username')
        group_name = request.data.get('group_name')
        
        try:
            user = User.objects.get(username=username)
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            return Response({"message": f"User {username} added to {group_name} group"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

# ... Mantén tus otros ViewSets (CartViewSet, OrderViewSet, OrderItemViewSet) ...

from .models import Cart
from .serializers import CartSerializer

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        unit_price = menuitem.price
        price = quantity * unit_price
        serializer.save(user=self.request.user, unit_price=unit_price, price=price)

from rest_framework.exceptions import PermissionDenied

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order, OrderItem, Cart
from .serializers import OrderSerializer
from rest_framework.exceptions import ValidationError

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name__in=['Managers', 'Delivery Crew']).exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        cart_items = Cart.objects.filter(user=self.request.user)
        if not cart_items.exists():
            raise ValidationError("No items in the cart to place an order.")
        
        total = sum(item.price for item in cart_items)
        order = serializer.save(user=self.request.user, total=total, date=timezone.now())
        
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price
            )
        
        cart_items.delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.user != request.user:
            raise PermissionDenied("You cannot delete this order.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['patch'], permission_classes=[IsManager])
    def assign_to_delivery_crew(self, request, pk=None):
        order = self.get_object()
        delivery_crew_id = request.data.get('delivery_crew_id')
        try:
            delivery_crew = User.objects.get(id=delivery_crew_id, groups__name='Delivery Crew')
            order.delivery_crew = delivery_crew
            order.save()
            return Response({'status': 'order assigned to delivery crew'})
        except User.DoesNotExist:
            return Response({'error': 'Invalid delivery crew user'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], permission_classes=[IsDeliveryCrew])
    def mark_as_delivered(self, request, pk=None):
        order = self.get_object()
        order.is_delivered = True
        order.save()
        return Response({'status': 'order marked as delivered'})

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    
    
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })




@api_view(['POST'])
@permission_classes([IsAdminUser])
def assign_user_to_group(request):
    username = request.data.get('username')
    group_name = request.data.get('group_name')
    
    try:
        user = User.objects.get(username=username)
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return Response({"message": f"User {username} added to {group_name} group"}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Group.DoesNotExist:
        return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_category(request):
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_menu_item(request):
    serializer = MenuItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)