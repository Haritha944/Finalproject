from django.shortcuts import render,redirect,get_object_or_404
from cart.models import Cart,CartItem,Address,Coupon,UserCoupons
from products.models import Product,ProductVariant
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from user.models import User
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from order.models import Order,OrderItem,Payment
import random
import datetime
import razorpay

# Create your views here.
#<!- Cart section --->
def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart

def addcart(request,product_id):
    variant = ProductVariant.objects.get(id=product_id)
    product = Product.objects.get(id=variant.product.id) #Get the product
    try:
        cart=Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id= _cart_id(request)
        )
    cart.save()
    try:
        cart_item = CartItem.objects.get(product=product,cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity = 1,
            cart=cart,
            variant=variant,

        )
        cart_item.save()
    #return HttpResponse(cart_item.product)
    return redirect('cart:cart')
        
def cart(request,total=0,quantity=0,cart_items=None):
    url = request.META.get('HTTP_REFERER')
    cart_id = _cart_id(request)
    tax=0
    value=0
    discount=0
    grand_total=0
    current_date = timezone.now()
    try:
        cart=Cart.objects.get(cart_id = cart_id)
        cart_items = CartItem.objects.filter(cart=cart,is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.discount_price * cart_item.quantity)
            quantity += cart_item.quantity
        value=total
        try:
            if 'coupon_code' in request.session:
                coupon_code = request.session['coupon_code']
                coupon = Coupon.objects.get(coupon_code=coupon_code)
                if coupon.start_date <= current_date <= coupon.end_date:
                    if value >= coupon.min_purchase:
                        if not UserCoupons.objects.filter(user=request.user, coupon=coupon, is_used=True).exists():
                            discount=float(coupon.coupon_discount)
                            value -= discount
        except Coupon.DoesNotExist:
            coupon=None
            messages.warning(request, 'Invalid coupon code.')
       
        tax = (2*value)/100
        grand_total = value + tax
    except ObjectDoesNotExist:
        pass  #just ignore
    context = {
        'subtotal':total,
        'value':value,
        'quantity':quantity,
        'cart_items':cart_items,
        'tax':tax,
        'grand_total':grand_total,
        'discount':discount,

    }

    return render(request,'cart/cart.html',context)

def removecartitem(request,product_id):
    cart_id = _cart_id(request)
    productvariant = get_object_or_404(ProductVariant,id = product_id)
    try:
        email = request.session['user-email']
        user = User.objects.get(email=email)
        cart_item = CartItem.objects.get(variant=productvariant,cart=cart)
    except:
        cart = Cart.objects.get(cart_id=cart_id)
        cart_item = CartItem.objects.get(variant=productvariant,cart=cart)
    cart_item.delete()
    return redirect('cart:cart')


#<!- Cart section End--->

#<!- User Profile section --->
@login_required
def profile(request):
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.get(email=email)
        name = request.POST.get('name')
        if name != user.name:
            if User.objects.filter(name=name).exists():
                messages.error(request, "username already exist..!")
                return redirect(url)
            else:
                user.name = request.POST.get('name')
                user.email = request.POST.get('email')
                user.mobile = request.POST.get('mobile')
                user.first_name = request.POST.get('firstname')
                user.last_name = request.POST.get('lastname')
                user.save()
        else:
            user.email = request.POST.get('email')
            user.mobile = request.POST.get('mobile')
            user.first_name = request.POST.get('firstname')
            user.last_name = request.POST.get('lastname')
            user.save()
    if request.user.is_authenticated:
        user = request.user
        context = {
            'user': user
        }
        return render(request, 'userprofile/profile.html',context)
   

    return redirect('user:handlelogin')

@login_required
def address(request):
    user = request.user
    addresses = Address.objects.filter(user_id=user)
    context = {
        'addresses': addresses
    }
    return render(request,'userprofile/address.html',context)
        

    
@login_required
def editaddress(request,address_id):
    if request.method=="POST":
        address = Address.objects.get(id=address_id)
        print(address)
        address.recipient_name = request.POST.get('RecipientName')
        address.email = request.POST.get('email')
        address.house_no = request.POST.get('house_no')
        address.mobile = request.POST.get('mobile')
        address.street_name = request.POST.get('street_name')
        address.village_name = request.POST.get('village_name')
        address.postal_code = request.POST.get('postal_code')
        address.district = request.POST.get('district')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country')
        default_address = request.POST.get('default_address')
        if default_address == 'on':
            try:
                email=request.user
                user=User.objects.get(email=email)
                addrss = Address.objects.get(user_id=user,is_default=True)
                addrss.is_default = False
                addrss.save()
            except Address.DoesNotExist:
                pass
        address.is_default= True
        address.save()
        addresses = Address.objects.filter(user_id=address.user_id)
        context = {
            "addresses":addresses
        }


    return render(request,'userprofile/address.html',context)


@login_required
def addaddress(request):
    email = request.POST.get('email')
    user=User.objects.get(email=email)
    default_address = request.POST.get('default_address')
    if default_address == 'on':
        try:
            adrss = Address.objects.get(user_id=user, is_default=True)
            
            adrss.is_default = False
            
            adrss.save()
        except Address.DoesNotExist:
            pass
    address = Address()
    address.user_id = user
    address.recipient_name = request.POST.get('RecipientName')
    address.email = request.POST.get('email')
    address.house_no = request.POST.get('house_no')
    address.mobile = request.POST.get('mobile')
    address.is_default=True
    address.email = request.POST.get('email')
    address.street_name = request.POST.get('street_name')
    address.village_name = request.POST.get('village_name')
    address.postal_code = request.POST.get('postal_code')
    address.district= request.POST.get('district')
    address.state = request.POST.get('state')
    address.country = request.POST.get('country')
    address.save()
    addresses = Address.objects.filter(user_id=user)
    context = {
            "addresses":addresses
        }
    return render(request,'userprofile/address.html',context)


def deleteaddress(request,address_id):
    address = Address.objects.get(id=address_id)
    if address is not None:
        address.delete()
        return redirect('cart:address')
    
@login_required
def checkout(request,total=0,quantity=0,cart_items=None):
    user=request.user
    url = request.META.get('HTTP_REFERER')
    discount=0
    try:
        email = request.POST.get('email')
        user=User.objects.get(user=request.user,email=email)
        
        if user is not None:
            cart_items = CartItem.objects.filter(user_id=user.id, is_active=True).order_by('id')
    except:
        cart_id = _cart_id(request)
        cart = Cart.objects.get(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')
        
           
        for cart_item in cart_items:
            total += (cart_item.variant.discount_price * cart_item.quantity)
            quantity += cart_item.quantity
        if 'coupon_code' in request.session:
            coupon_code = request.session['coupon_code']
            try:
                coupon = Coupon.objects.get(coupon_code=coupon_code)
                if coupon.start_date <= timezone.now() <= coupon.end_date:
                    value=total
                    if value >= coupon.min_purchase:
                    # Apply the coupon discount
                        discount = float(coupon.coupon_discount)
                        value -= discount
            except Coupon.DoesNotExist:
                messages.warning(request, 'Invalid coupon code')
        else:
            value=total
    
                
        tax = (2 * value) / 100
        grand_total = value + tax
       
    address_list = Address.objects.filter(user_id=request.user)
    default_address = address_list.filter(user_id=request.user).first()
    if not default_address:
        return redirect('cart:address')
    

    context = {
        'total':total,
        'value':value,
        'quantity':quantity,
        'grand_total':grand_total,
        'cart_items': cart_items,
        'tax': tax,
        'discount':discount,
        'address_list':address_list,
        'default_address': default_address,
    }

    return render(request,'cart/checkout2.html',context)
@login_required
def set_default_address(request, address_id):
    addr_list = Address.objects.filter(email=request.user.email)
    for a in addr_list:
        a.is_default = False
        a.save()
    address = Address.objects.get(id=address_id)
    address.is_default=True
    address.save()
    return redirect('cart:checkout')
def addaddresscheck(request):
    email = request.POST.get('email')
    user=User.objects.get(email=request.user.email)
    try:
        uname = request.POST.get('RecipientName')
        print(uname)
        if Address.objects.filter(user_id=user, recipient_name=uname).exists():
            print("error")
            messages.error("This user address already exist..!")
            return redirect('cart:checkout')
        else:
            print("yes")
            address = Address()
            address.user_id = user
            address.recipient_name = request.POST.get('RecipientName')
            address.email = request.POST.get('email')
            address.house_no = request.POST.get('house_no')
            address.street_name = request.POST.get('street_name')
            address.village_name = request.POST.get('village_name')
            address.postal_code = request.POST.get('postal_code')
            address.district = request.POST.get('district')
            address.state = request.POST.get('state')
            address.mobile = request.POST.get('mobile')
            address.country = request.POST.get('country')
            address.save()
            return redirect('cart:checkout')
    except:
        messages.error(request, "This user address already exist..!")
        return redirect('cart:checkout',new_address_id=address.id)

def removecart(request, product_id):  
    cart_id = _cart_id(request)  # Get or generate the cart_id
    productvariant = get_object_or_404(ProductVariant, id=product_id)
    print(productvariant)
    try:
        email = request.user
        user=User.objects.get(email=request.user.email)
        cart_item = CartItem.objects.get(variant=productvariant, user_id=user.id)
        print(cart_item)

    except:
        cart = Cart.objects.get(cart_id=cart_id)
        cart_item = CartItem.objects.get(variant=productvariant, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        sub_total = 0
        try:
            cart_item = CartItem.objects.get(variant=productvariant, cart=cart, user=request.user)
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        except:
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            sub_total += (item.variant.discount_price * item.quantity)         
        total = cart_item.quantity * cart_item.variant.discount_price
        return JsonResponse({'quantity': cart_item.quantity, 'total': total,'sub_total': sub_total})
        
    else:
        cart_item.delete()
        return JsonResponse({'status': 'empty'})


@login_required
def placeorder(request, total=0, quantity=0):
    
    if request.method == 'POST':
        email = request.user
        user = User.objects.get(email=email)
        print(user)
        cart_id = _cart_id(request)
        cart = Cart.objects.get(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by('id')
        print(cart_items)
        total = 0
        discount=0
        grand_total=0
        tax=0
        quantity = 0
        for cart_item in cart_items:
            total += (cart_item.variant.discount_price * cart_item.quantity)
            quantity += cart_item.quantity
        
        if 'coupon_code' in request.session:
            value=total
            coupon_code = request.session['coupon_code']
            try:
                coupon = Coupon.objects.get(coupon_code=coupon_code)
                if coupon.start_date <= timezone.now() <= coupon.end_date and total >= coupon.min_purchase:
                            # Apply the coupon discount
                    discount = float(coupon.coupon_discount)
                    value -= discount

                    # Mark coupon as used for the user
                    used_coupon = UserCoupons.objects.create(
                        user=user,
                        coupon=coupon,
                        is_used=True
                    )
                    used_coupon.save()
                    
            except Coupon.DoesNotExist:
                messages.warning(request, 'Invalid coupon code')
        else:
            value=total
        tax = (2 * value) / 100
        grand_total = value + tax 
        print(grand_total)
        
        if user is not None:
            try:
                #address=Address.objects.filter(user_id=user.id).last()
                address=Address.objects.get(email=request.user.email,is_default=True)
            except:
                messages.error(request,"Create a address...!")
                return redirect('cart:address')
                
        else:
            address=Address.objects.filter(email=user.email).last()
        
        
        order = Order()
        order.user = user
        order.total_price=grand_total
        order.address = address
        trackno = 'pvkewt' + str(random.randint(1111111, 9999999))
        while Order.objects.filter(tracking_no=trackno) is None:
            trackno = 'pvkewt' + str(random.randint(1111111, 9999999))
        order.tracking_no = trackno
       
        order.save()
        neworderitems = CartItem.objects.filter(user=user, is_active=True)
        for item in neworderitems:
            if 'coupon_code' in request.session:
                coupon_code = request.session['coupon_code']
                coupon = Coupon.objects.get(coupon_code=coupon_code)
                discount = float(coupon.coupon_discount)
                price=item.variant.discount_price-discount
                del request.session['coupon_code']
            else:
                price=item.variant.discount_price

            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                price=price,
                quantity=item.quantity,
                user=user
            )
            # reduce the product quantity from available stock
            orderproduct = ProductVariant.objects.get(
                id=item.variant.id
                )
            print(orderproduct.stock)
            orderproduct.stock = orderproduct.stock - item.quantity
            print(orderproduct.stock)
            orderproduct.save()

            # delete cart
            try:
                Cart.objects.get(cart_id= item.cart.cart_id).delete()
            except:
                pass
        order = Order.objects.get(user=user,tracking_no=trackno,total_price=grand_total)
        bulk_order_id=order.id
        r_tot=order.total_price*100
        
        context = {
            'order': order,
            'address':address,
            'cart_items': cart_items,
            'total_price': grand_total,
            'tracking_no':trackno,
            'tax': tax,
            'discount': discount,
            'total': total ,
            'value':value,
            'r_tot':r_tot,
            'quantity': quantity,
            "callback_url": "https://" + "www.trendyfoot.online" + "/callback/?order_id={}".format(bulk_order_id),
            "razorpay_key":"rzp_test_zLLrBmHDjYzLTa",
            
        }

        return render(request, 'order/placeorder.html', context)
    else:
        return redirect('cart:checkout')
    
def increment(request, product_id):
    cart_id = _cart_id(request)  # Get or generate the cart_id
    productvariant = get_object_or_404(ProductVariant, id=product_id)

    try:
        email = request.user
        user = User.objects.get(email=email)
        cart_item = CartItem.objects.get(variant=productvariant, user=user)
        print(cart_item)
    except:
        cart = Cart.objects.get(cart_id=cart_id)
        cart_item = CartItem.objects.get(variant=productvariant, cart=cart)
        print(cart_item)

    if productvariant.stock <= cart_item.quantity:

        sub_total = 0
        try:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        except:
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            sub_total += (item.variant.discount_price * item.quantity)
        total = cart_item.quantity * cart_item.variant.discount_price
        print("hii",sub_total)
        return JsonResponse(
            {'quantity': cart_item.quantity, 'total': total, 'sub_total': sub_total, 'messages': "error"})
    # if cart_item.quantity > 1:
    else:
        cart_item.quantity += 1
        cart_item.save()
        # calculating subtotal
        sub_total = 0
        try:
            print(request.user)
            cart_item = CartItem.objects.get(variant=productvariant, cart=cart, user=request.user)
            cart_items = CartItem.objects.filter(user=request.user,is_active=True)
            print(cart_items)
        except:
            
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart,is_active=True)
            print(cart_items)
        for item in cart_items:
            sub_total += (item.variant.discount_price * item.quantity)
        total = cart_item.quantity * cart_item.variant.discount_price
        print("hii",sub_total)
        return JsonResponse(
            {'quantity': cart_item.quantity, 'total': total, 'sub_total': sub_total, "messages": "success"})
    
