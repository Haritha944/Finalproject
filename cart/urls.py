from django.urls import path
from . import views

app_name='cart'

urlpatterns = [
    # user side
    path('cart/', views.cart, name='cart'),
    path('addcart/<int:product_id>/', views.addcart, name='addcart'),
    path('removecartitem/<int:product_id>/', views.removecartitem,
         name='removecartitem'),
    path('profile/', views.profile, name='profile'),
    path('address/', views.address, name='address'),
    path('addaddress/', views.addaddress, name='addaddress'),
    path('editaddress/<int:address_id>', views.editaddress, name='editaddress'),
    path('deleteaddress/<int:address_id>', views.deleteaddress, name='deleteaddress'),
    path('checkout/', views.checkout, name='checkout'),
    path('addaddresscheck/', views.addaddresscheck,
         name='addaddresscheck'),
    path('set_default_address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('removecart/<int:product_id>/', views.removecart, name='removecart'),
    path('placeorder/', views.placeorder, name='placeorder'),
    path('increment/<int:product_id>/', views.increment,name='increment'),
    
    

]