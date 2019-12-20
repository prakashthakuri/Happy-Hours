
from django.urls import path

from .views import (
    ItemDetailView,
    CheckoutView,
ProfileView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    PaymentView,
    LandingView,
    AddCouponView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('landing_page/', LandingView.as_view(), name='landing_page'),
    path('profile/', ProfileView.as_view(), name='profile'),

    path('checkout/', CheckoutView.as_view(), name='checkout'),

    path('order_summary/', OrderSummaryView.as_view(), name='order_summary'),

    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),

    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-single-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),

]

