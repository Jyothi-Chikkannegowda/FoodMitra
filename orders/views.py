from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Order, Payment
from menu.models import MenuItem
from accounts.models import CookProfile, CustomerProfile
from accounts.geocoding import haversine_km
import razorpay
from django.http import HttpResponse
from .pdf_generator import generate_receipt_pdf

# Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def get_packing_charge(quantity):
    if quantity <= 2:
        return 10
    elif quantity <= 5:
        return 20
    else:
        return 30


@login_required
def order_list(request):
    orders = Order.objects.filter(
        customer=request.user
    ).exclude(status='awaiting_payment').order_by('-order_time')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def place_order(request, menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        delivery_type = request.POST.get('delivery_type')
        payment_method = request.POST.get('payment_method', 'online')

        if quantity > menu_item.quantity_available:
            messages.error(request, f'Only {menu_item.quantity_available} plates available!')
            return render(request, 'orders/place_order.html', {'menu_item': menu_item})

        # Distance check
        try:
            customer_profile = CustomerProfile.objects.get(user=request.user)
            customer_lat = customer_profile.latitude
            customer_lng = customer_profile.longitude
        except CustomerProfile.DoesNotExist:
            customer_lat = None
            customer_lng = None

        cook_lat = menu_item.cook.latitude
        cook_lng = menu_item.cook.longitude
        has_customer_location = customer_lat is not None and customer_lng is not None

        if has_customer_location and cook_lat is not None and cook_lng is not None:
            distance = haversine_km(customer_lat, customer_lng, cook_lat, cook_lng)
            if distance > 5:
                messages.error(
                    request,
                    f'This cook is {distance:.1f}km away - outside our 5km delivery range.'
                )
                return render(request, 'orders/place_order.html', {'menu_item': menu_item})

        food_price = float(menu_item.price) * quantity
        delivery_charge = 20 if delivery_type == 'delivery' else 0
        platform_fee = 2
        packing_charge = get_packing_charge(quantity)
        gst = round((food_price + delivery_charge + platform_fee + packing_charge) * 0.05, 2)

        # ---------- CASH ON DELIVERY ----------
        if payment_method == 'cod':
            total_cod = food_price + delivery_charge + platform_fee + packing_charge + gst

            order = Order.objects.create(
                customer=request.user,
                cook=menu_item.cook,
                menu_item=menu_item,
                quantity=quantity,
                total_price=total_cod,
                delivery_type=delivery_type,
                status='pending'
            )

            menu_item.quantity_available -= quantity
            if menu_item.quantity_available == 0:
                menu_item.is_available = False
            menu_item.save()

            Payment.objects.create(
                order=order,
                amount=total_cod,
                payment_method='cod',
                status='pending',
            )

            return render(request, 'orders/cod_confirmation.html', {
                'order': order,
                'food_price': food_price,
                'delivery_charge': delivery_charge,
                'platform_fee': platform_fee,
                'packing_charge': packing_charge,
                'gst': gst,
                'total_price_display': total_cod,
            })

        # ---------- ONLINE PAYMENT (Razorpay) ----------
        total_price = food_price + delivery_charge + platform_fee + packing_charge + gst

        order = Order.objects.create(
            customer=request.user,
            cook=menu_item.cook,
            menu_item=menu_item,
            quantity=quantity,
            total_price=total_price,
            delivery_type=delivery_type,
            status='awaiting_payment'
        )

        menu_item.quantity_available -= quantity
        if menu_item.quantity_available == 0:
            menu_item.is_available = False
        menu_item.save()

        razorpay_order = razorpay_client.order.create({
            'amount': int(total_price * 100),
            'currency': 'INR',
            'payment_capture': 1
        })

        Payment.objects.create(
            order=order,
            amount=total_price,
            payment_method='razorpay',
            status='pending',
            transaction_id=razorpay_order['id']
        )

        return render(request, 'orders/payment.html', {
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'total_price': int(total_price * 100),
            'user_name': request.user.first_name,
            'user_email': request.user.email,
            'food_price': food_price,
            'delivery_charge': delivery_charge,
            'platform_fee': platform_fee,
            'packing_charge': packing_charge,
            'gst': gst,
            'total_price_display': total_price,
        })

    return render(request, 'orders/place_order.html', {'menu_item': menu_item})


@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        print(f"Payment ID: {razorpay_payment_id}")
        print(f"Order ID: {razorpay_order_id}")
        print(f"Signature: {razorpay_signature}")

        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            print("Signature verified successfully!")

            payment = Payment.objects.get(transaction_id=razorpay_order_id)
            payment.status = 'success'
            payment.save()

            order = payment.order
            order.status = 'accepted'
            order.save()

            # Send email to customer
            try:
                send_mail(
                    subject=f'FoodMitra - Order #{order.id} Confirmed! 🎉',
                    message=f'''
Dear {order.customer.first_name},

Your order has been confirmed and payment received!

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Cook: {order.cook.user.first_name} {order.cook.user.last_name}
Quantity: {order.quantity} plate(s)
Delivery type: {order.delivery_type}

BILL SUMMARY
Food price: Rs.{order.menu_item.price * order.quantity}
Delivery charge: Rs.{20 if order.delivery_type == 'delivery' else 0}
Packing charge: Rs.{get_packing_charge(order.quantity)}
Platform fee: Rs.2
GST (5%): included
Total Amount: Rs.{payment.amount}

Payment ID: {razorpay_payment_id}
Payment Status: Success

Thank you for ordering from FoodMitra!
Enjoy your home cooked meal!

Regards,
Team FoodMitra
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer.email],
                    fail_silently=True,
                )
                print("Customer email sent!")
            except Exception as e:
                print(f"Customer email error: {e}")

            # Send email to cook
            try:
                send_mail(
                    subject=f'FoodMitra - New Order #{order.id} Received! 🍛',
                    message=f'''
Dear {order.cook.user.first_name},

You have received a new online order!

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Quantity: {order.quantity} plate(s)
Delivery type: {order.delivery_type}
Total Amount: Rs.{order.total_price}

CUSTOMER DETAILS
Customer name: {order.customer.first_name} {order.customer.last_name}
Customer email: {order.customer.email}

Please login to FoodMitra and accept the order as soon as possible!

Thank you,
Team FoodMitra
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.cook.user.email],
                    fail_silently=True,
                )
                print("Cook email sent!")
            except Exception as e:
                print(f"Cook email error: {e}")

            return redirect('order_tracking', order_id=order.id)

        except Exception as e:
            print(f"Payment verification error: {e}")
            return redirect('payment_failed')

    return redirect('home')


def payment_failed(request):
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id, status='awaiting_payment')
            menu_item = order.menu_item
            menu_item.quantity_available += order.quantity
            menu_item.is_available = True
            menu_item.save()

            try:
                payment = Payment.objects.get(order=order)
                payment.status = 'failed'
                payment.save()
            except Payment.DoesNotExist:
                pass

            order.status = 'rejected'
            order.save()
        except Order.DoesNotExist:
            pass

    return render(request, 'orders/payment_failed.html')


@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'orders/order_tracking.html', {'order': order})


@login_required
def cook_orders(request):
    try:
        cook_profile = CookProfile.objects.get(user=request.user)
        orders = Order.objects.filter(
            cook=cook_profile
        ).exclude(status='awaiting_payment').order_by('-order_time')
        return render(request, 'orders/cook_orders.html', {'orders': orders})
    except CookProfile.DoesNotExist:
        return redirect('dashboard')


@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()

        try:
            if new_status == 'accepted':
                send_mail(
                    subject=f'FoodMitra - Order #{order.id} Accepted! 🎉',
                    message=f'''
Dear {order.customer.first_name},

Great news! Your order has been accepted by the cook!

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Cook: {order.cook.user.first_name} {order.cook.user.last_name}
Quantity: {order.quantity} plate(s)
Delivery type: {order.delivery_type}
Total Amount: Rs.{order.total_price}

Your food is being prepared with love! 🍛

Thank you for ordering from FoodMitra!

Regards,
Team FoodMitra
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer.email],
                    fail_silently=True,
                )

            elif new_status == 'preparing':
                send_mail(
                    subject=f'FoodMitra - Order #{order.id} is Being Prepared! 👩‍🍳',
                    message=f'''
Dear {order.customer.first_name},

Your food is being prepared right now!

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Cook: {order.cook.user.first_name} {order.cook.user.last_name}

Your delicious meal will be ready soon! 🍛

Thank you for ordering from FoodMitra!

Regards,
Team FoodMitra
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer.email],
                    fail_silently=True,
                )

            elif new_status == 'ready':
                if order.delivery_type == 'pickup':
                    message_body = f'''
Dear {order.customer.first_name},

Your order is ready for pickup! 🎉

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}

PICKUP ADDRESS
{order.cook.home_address}

Please come and collect your order! 😊

Thank you for ordering from FoodMitra!

Regards,
Team FoodMitra
                    '''
                else:
                    message_body = f'''
Dear {order.customer.first_name},

Your order is ready and will be delivered soon! 🚀

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Cook: {order.cook.user.first_name} {order.cook.user.last_name}

Your food is on its way! 🍛

Thank you for ordering from FoodMitra!

Regards,
Team FoodMitra
                    '''
                send_mail(
                    subject=f'FoodMitra - Order #{order.id} is Ready! 🎉',
                    message=message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer.email],
                    fail_silently=True,
                )

            elif new_status == 'delivered':
                send_mail(
                    subject=f'FoodMitra - Order #{order.id} Delivered! 😊',
                    message=f'''
Dear {order.customer.first_name},

Your order has been delivered! Enjoy your meal! 🍛

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Cook: {order.cook.user.first_name} {order.cook.user.last_name}
Total Amount: Rs.{order.total_price}

We hope you enjoyed your home cooked meal!
Please take a moment to rate your experience! ⭐

Thank you for ordering from FoodMitra!

Regards,
Team FoodMitra
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer.email],
                    fail_silently=True,
                )

            elif new_status == 'rejected':
                send_mail(
                    subject=f'FoodMitra - Order #{order.id} Cancelled 😞',
                    message=f'''
Dear {order.customer.first_name},

We are sorry! Your order has been cancelled by the cook.

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Cook: {order.cook.user.first_name} {order.cook.user.last_name}

If you paid online, your refund will be processed within 5-7 business days.

Please try ordering from another cook!

Thank you for ordering from FoodMitra!

Regards,
Team FoodMitra
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer.email],
                    fail_silently=True,
                )
        except Exception as e:
            print(f"Status email error: {e}")

    return redirect('cook_orders')


@login_required
def download_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    try:
        payment = Payment.objects.get(order=order, status='success')
    except Payment.DoesNotExist:
        class DummyPayment:
            transaction_id = f'CASH_{order_id}'
            amount = order.total_price
            status = 'success'
        payment = DummyPayment()

    buffer = generate_receipt_pdf(order, payment)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="FoodMitra_Receipt_Order_{order_id}.pdf"'
    return response


@login_required
def cod_confirm(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = Order.objects.get(id=order_id, customer=request.user)
            order.status = 'pending'
            order.save()

            # Send confirmation email to customer
            try:
                send_mail(
                    subject=f'FoodMitra - COD Order #{order.id} Placed! 🍛',
                    message=f'''
Dear {order.customer.first_name},

Your Cash on Delivery order has been placed!

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Cook: {order.cook.user.first_name} {order.cook.user.last_name}
Quantity: {order.quantity} plate(s)
Delivery type: {order.delivery_type}
Packing charge: Rs.{get_packing_charge(order.quantity)}
Total Amount: Rs.{order.total_price}
Payment: Cash on Delivery

Please keep cash ready when your order arrives!

Thank you for ordering from FoodMitra!

Regards,
Team FoodMitra
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.customer.email],
                    fail_silently=True,
                )
                print("Customer COD email sent!")
            except Exception as e:
                print(f"Customer COD email error: {e}")

            # Send notification email to cook
            try:
                send_mail(
                    subject=f'FoodMitra - New COD Order #{order.id} Received! 🍛',
                    message=f'''
Dear {order.cook.user.first_name},

You have received a new Cash on Delivery order!

ORDER DETAILS
Order ID: #{order.id}
Food item: {order.menu_item.food_name}
Quantity: {order.quantity} plate(s)
Delivery type: {order.delivery_type}
Total Amount: Rs.{order.total_price}
Payment: Cash on Delivery

CUSTOMER DETAILS
Customer name: {order.customer.first_name} {order.customer.last_name}
Customer email: {order.customer.email}

Please login to FoodMitra and accept the order as soon as possible!

Thank you,
Team FoodMitra
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.cook.user.email],
                    fail_silently=False,
                )
                print("Cook COD email sent!")
            except Exception as e:
                print(f"Cook COD email error: {e}")

            return redirect('order_tracking', order_id=order.id)
        except Order.DoesNotExist:
            return redirect('dashboard')
    return redirect('dashboard')
