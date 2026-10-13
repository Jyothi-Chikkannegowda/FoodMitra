from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MenuItem
from accounts.models import CookProfile, CustomerProfile
from accounts.geocoding import haversine_km
from datetime import date, timedelta, datetime

MAX_DELIVERY_RADIUS_KM = 5


def _annotate_distance(menu_items, customer_lat, customer_lng):
    have_customer_location = customer_lat is not None and customer_lng is not None

    for item in menu_items:
        cook_lat = item.cook.latitude
        cook_lng = item.cook.longitude

        if have_customer_location and cook_lat is not None and cook_lng is not None:
            distance = haversine_km(customer_lat, customer_lng, cook_lat, cook_lng)
            item.distance = round(distance, 1)
            item.in_range = distance <= MAX_DELIVERY_RADIUS_KM
        else:
            item.distance = None
            item.in_range = True

    return menu_items


def _get_customer_coords(request):
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        return profile.latitude, profile.longitude
    except CustomerProfile.DoesNotExist:
        return None, None


@login_required
def menu_list(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    now = datetime.now()
    can_preorder = now.hour < 21

    customer_lat, customer_lng = _get_customer_coords(request)

    all_menus = list(MenuItem.objects.filter(
        is_available=True,
        cook__is_available=True
    ).exclude(available_date=tomorrow).order_by('-created_at'))

    tomorrow_menus = list(MenuItem.objects.filter(
        is_available=True,
        cook__is_available=True,
        available_date=tomorrow
    ))

    all_menus = _annotate_distance(all_menus, customer_lat, customer_lng)
    tomorrow_menus = _annotate_distance(tomorrow_menus, customer_lat, customer_lng)

    return render(request, 'menu/menu_list.html', {
        'menus': all_menus,
        'tomorrow_menus': tomorrow_menus,
        'today': today,
        'tomorrow': tomorrow,
        'has_customer_location': customer_lat is not None,
        'customer_lat': customer_lat,
        'customer_lng': customer_lng,
        'max_radius_km': MAX_DELIVERY_RADIUS_KM,
        'can_preorder': can_preorder,
    })


@login_required
def post_menu(request):
    try:
        cook_profile = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        return redirect('dashboard')

    if not cook_profile.is_verified:
        return render(request, 'menu/not_verified.html')

    error = None

    if request.method == 'POST':
        food_name = request.POST.get('food_name')
        description = request.POST.get('description')
        price = float(request.POST.get('price', 0))
        quantity = int(request.POST.get('quantity', 0))
        cuisine_type = request.POST.get('cuisine_type')
        photo = request.FILES.get('photo')
        available_date_str = request.POST.get('available_date')
        is_preorder = request.POST.get('is_preorder') == 'on'

        # is_veg is derived from cook's kitchen_type
        # Pure Veg cook → always veg, Non-Veg cook → always nonveg
        is_veg = (cook_profile.kitchen_type == 'veg')

        now = datetime.now()

        if is_preorder and now.hour >= 21:
            error = 'Pre-orders are closed after 9 PM! Please post for today only.'
        elif price < 10:
            error = 'Price must be at least ₹10!'
        elif price > 1500:
            error = 'Price cannot exceed ₹500!'
        elif quantity < 1:
            error = 'Quantity must be at least 1!'
        elif quantity > 50:
            error = 'Quantity cannot exceed 50!'
        elif not food_name:
            error = 'Food name is required!'
        elif not cuisine_type:
            error = 'Please select cuisine type!'
        else:
            if available_date_str:
                available_date = date.fromisoformat(available_date_str)
            else:
                available_date = date.today()

            menu_item = MenuItem.objects.create(
                cook=cook_profile,
                food_name=food_name,
                description=description,
                price=price,
                quantity_available=quantity,
                cuisine_type=cuisine_type,
                is_veg=is_veg,
                photo=photo,
                is_available=True,
                available_date=available_date,
                is_preorder=is_preorder
            )
            # Auto mark unavailable if quantity is 0
            if quantity == 0:
                menu_item.is_available = False
                menu_item.save()
            return redirect('dashboard')

    today = date.today()
    tomorrow = today + timedelta(days=1)

    return render(request, 'menu/post_menu.html', {
        'cook': cook_profile,
        'error': error,
        'today': today,
        'tomorrow': tomorrow,
    })


@login_required
def edit_menu(request, menu_id):
    cook = get_object_or_404(CookProfile, user=request.user)
    menu = get_object_or_404(MenuItem, id=menu_id, cook=cook)

    if request.method == "POST":
        menu.food_name = request.POST.get("food_name")
        menu.description = request.POST.get("description")
        menu.price = float(request.POST.get("price"))
        menu.quantity_available = int(request.POST.get("quantity"))
        menu.cuisine_type = request.POST.get("cuisine_type")

        # is_veg always matches cook's kitchen_type
        menu.is_veg = (cook.kitchen_type == 'veg')

        # Auto mark unavailable if quantity is 0
        if menu.quantity_available == 0:
            menu.is_available = False
        else:
            menu.is_available = True

        menu.is_preorder = request.POST.get("is_preorder") == "on"

        available_date = request.POST.get("available_date")
        if available_date:
            menu.available_date = available_date

        if request.FILES.get("photo"):
            menu.photo = request.FILES["photo"]

        menu.save()
        messages.success(request, 'Menu item updated successfully!')
        return redirect("my_menu")

    return render(request, "menu/edit_menu.html", {
        "menu": menu
    })


@login_required
def delete_menu(request, menu_id):
    cook = get_object_or_404(CookProfile, user=request.user)
    menu = get_object_or_404(MenuItem, id=menu_id, cook=cook)

    if request.method == "POST":
        menu.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect("my_menu")

    return render(request, "menu/delete_menu.html", {
        "menu": menu
    })


@login_required
def my_menu(request):
    try:
        cook = CookProfile.objects.get(user=request.user)
    except CookProfile.DoesNotExist:
        messages.error(request, "Only cooks can access My Menu.")
        return redirect("dashboard")

    now = datetime.now()
    can_preorder = now.hour < 21

    menus = MenuItem.objects.filter(cook=cook).order_by("-created_at")

    return render(request, "menu/my_menu.html", {
        "cook": cook,
        "menus": menus,
        "can_preorder": can_preorder,
    })