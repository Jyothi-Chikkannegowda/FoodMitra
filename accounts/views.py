from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from orders.models import Order
from .models import CookProfile, CustomerProfile
from .geocoding import geocode_address
from django.db.models import Sum

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        role = request.POST.get('role')

        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken!')
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        home_address = request.POST.get('home_address')

        if role == 'cook':
            aadhaar = request.POST.get('aadhaar')
            speciality = request.POST.get('speciality')
            kitchen_type = request.POST.get('kitchen_type', 'veg')
            lat, lng = geocode_address(home_address)

            CookProfile.objects.create(
                user=user,
                home_address=home_address,
                phone=phone,
                aadhaar_number=aadhaar,
                speciality=speciality,
                is_verified=False,
                is_available=True,
                latitude=lat,
                longitude=lng,
                kitchen_type=kitchen_type,
            )
        else:
            lat, lng = geocode_address(home_address)

            CustomerProfile.objects.create(
                user=user,
                address=home_address,
                phone=phone,
                latitude=lat,
                longitude=lng,
            )

        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('dashboard')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if remember:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
            else:
                request.session.set_expiry(0)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password!')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_superuser:
        return redirect('admin_dashboard')

    try:
        cook_profile = CookProfile.objects.get(user=request.user)
        from orders.models import Order
        from menu.models import MenuItem
        from datetime import timedelta, datetime, time
        from django.utils import timezone

        total_orders = Order.objects.filter(cook=cook_profile).exclude(status='awaiting_payment').count()
        total_earnings = sum(o.total_price for o in Order.objects.filter(cook=cook_profile, status='delivered'))
        total_menu_items = MenuItem.objects.filter(cook=cook_profile).count()
        recent_orders = Order.objects.filter(cook=cook_profile).exclude(status='awaiting_payment').order_by('-order_time')[:5]

        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())

        def get_day_earnings(day_date):
            start = timezone.make_aware(datetime.combine(day_date, time.min))
            end = start + timedelta(days=1)
            orders = Order.objects.filter(
                cook=cook_profile,
                status='delivered',
                order_time__gte=start,
                order_time__lt=end
            )
            return float(sum(o.total_price for o in orders))

        mon_earnings = get_day_earnings(week_start)
        tue_earnings = get_day_earnings(week_start + timedelta(days=1))
        wed_earnings = get_day_earnings(week_start + timedelta(days=2))
        thu_earnings = get_day_earnings(week_start + timedelta(days=3))
        fri_earnings = get_day_earnings(week_start + timedelta(days=4))
        sat_earnings = get_day_earnings(week_start + timedelta(days=5))
        sun_earnings = get_day_earnings(week_start + timedelta(days=6))

        return render(request, 'accounts/cook_dashboard.html', {
            'cook_profile': cook_profile,
            'total_orders': total_orders,
            'total_earnings': total_earnings,
            'total_menu_items': total_menu_items,
            'recent_orders': recent_orders,
            'mon_earnings': mon_earnings,
            'tue_earnings': tue_earnings,
            'wed_earnings': wed_earnings,
            'thu_earnings': thu_earnings,
            'fri_earnings': fri_earnings,
            'sat_earnings': sat_earnings,
            'sun_earnings': sun_earnings,
        })
    except CookProfile.DoesNotExist:
        pass

    try:
        customer_profile = CustomerProfile.objects.get(user=request.user)
        from orders.models import Order
        recent_orders = Order.objects.filter(customer=request.user).exclude(
            status='awaiting_payment'
        ).order_by('-order_time')[:5]
        return render(request, 'accounts/customer_dashboard.html', {
            'recent_orders': recent_orders,
        })
    except CustomerProfile.DoesNotExist:
        pass

    return render(request, 'accounts/dashboard.html')


def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('home')

    from orders.models import Order
    from menu.models import MenuItem

    total_users = User.objects.count()
    total_cooks = CookProfile.objects.count()
    total_customers = CustomerProfile.objects.count()
    total_orders = Order.objects.exclude(status='awaiting_payment').count()
    total_menu_items = MenuItem.objects.count()
    pending_cooks = CookProfile.objects.filter(is_verified=False)
    verified_cooks = CookProfile.objects.filter(is_verified=True)
    recent_orders = Order.objects.exclude(status='awaiting_payment').order_by('-order_time')[:10]
    total_earnings = sum(o.total_price for o in Order.objects.filter(status='delivered'))

    return render(request, 'accounts/admin_dashboard.html', {
        'total_users': total_users,
        'total_cooks': total_cooks,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_menu_items': total_menu_items,
        'pending_cooks': pending_cooks,
        'verified_cooks': verified_cooks,
        'recent_orders': recent_orders,
        'total_earnings': total_earnings,
    })


def verify_cook(request, cook_id):
    if not request.user.is_superuser:
        return redirect('home')
    cook = CookProfile.objects.get(id=cook_id)
    cook.is_verified = True
    cook.save()
    return redirect('admin_dashboard')


from datetime import timedelta
from django.utils import timezone


@login_required
def earnings(request):
    try:
        cook_profile = CookProfile.objects.get(user=request.user)

        all_orders = Order.objects.filter(
            cook=cook_profile,
            status="delivered"
        ).order_by("-order_time")

        total_earnings = sum(order.total_price for order in all_orders)

        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        weekly_earnings = 0
        monthly_earnings = 0

        for order in all_orders:
            order_date = timezone.localtime(order.order_time).date()
            if week_start <= order_date <= today:
                weekly_earnings += order.total_price
            if month_start <= order_date <= today:
                monthly_earnings += order.total_price

        return render(request, "accounts/earnings.html", {
            "cook_profile": cook_profile,
            "total_earnings": total_earnings,
            "weekly_earnings": weekly_earnings,
            "monthly_earnings": monthly_earnings,
            "all_orders": all_orders,
        })

    except CookProfile.DoesNotExist:
        return redirect("dashboard")


@login_required
def profile(request):
    try:
        cook_profile = CookProfile.objects.get(user=request.user)
        return render(request, 'accounts/cook_profile.html', {
            'cook_profile': cook_profile,
        })
    except CookProfile.DoesNotExist:
        pass

    try:
        customer_profile = CustomerProfile.objects.get(user=request.user)
        return render(request, 'accounts/customer_profile.html', {
            'customer_profile': customer_profile,
        })
    except CustomerProfile.DoesNotExist:
        pass

    return render(request, 'accounts/dashboard.html')


@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        try:
            cook_profile = CookProfile.objects.get(user=user)
            cook_profile.speciality = request.POST.get('speciality', cook_profile.speciality)
            cook_profile.bio = request.POST.get('bio', cook_profile.bio)
            cook_profile.phone = request.POST.get('phone', cook_profile.phone)
            cooking_since = request.POST.get('cooking_since')
            if cooking_since:
                cook_profile.cooking_since = cooking_since
            if request.FILES.get('profile_photo'):
                cook_profile.profile_photo = request.FILES['profile_photo']
            cook_profile.save()
        except CookProfile.DoesNotExist:
            try:
                customer_profile = CustomerProfile.objects.get(user=user)
                if request.FILES.get('profile_photo'):
                    customer_profile.profile_photo = request.FILES['profile_photo']
                customer_profile.phone = request.POST.get('phone', customer_profile.phone)
                customer_profile.address = request.POST.get('address', customer_profile.address)
                customer_profile.save()
            except CustomerProfile.DoesNotExist:
                pass

    return redirect('profile')


@login_required
def toggle_availability(request):
    try:
        cook_profile = CookProfile.objects.get(user=request.user)
        cook_profile.is_available = not cook_profile.is_available
        cook_profile.save()
        if cook_profile.is_available:
            messages.success(request, '✅ You are now Available! Customers can see your food!')
        else:
            messages.success(request, '🔴 You are now On Leave! Your food is hidden from customers!')
    except CookProfile.DoesNotExist:
        pass
    return redirect('dashboard')


def terms(request):
    return render(request, 'terms.html')


def privacy(request):
    return render(request, 'privacy.html')


def contact(request):
    success = False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        try:
            from django.core.mail import send_mail
            send_mail(
                f'FoodMitra Complaint: {subject}',
                f'From: {name}\nEmail: {email}\n\nMessage:\n{message}',
                email,
                ['jyothicgowda.mys@gmail.com'],
                fail_silently=False,
            )
            success = True
        except:
            success = False
    return render(request, 'contact.html', {'success': success})