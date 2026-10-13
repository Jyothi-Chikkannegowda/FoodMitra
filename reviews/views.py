from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Review
from orders.models import Order
from accounts.models import CookProfile


@login_required
def review_list(request):
    # A cook has a related CookProfile; a customer doesn't.
    try:
        cook_profile = request.user.cookprofile
    except CookProfile.DoesNotExist:
        cook_profile = None

    if cook_profile:
        # Cook view: reviews customers have left about THEIR food
        reviews = Review.objects.filter(cook=cook_profile).order_by('-created_at')
        return render(request, 'reviews/review_list_cook.html', {
            'reviews': reviews,
            'cook_profile': cook_profile,
        })

    # Customer view: reviews the logged-in user has written
    reviews = Review.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'reviews/review_list.html', {'reviews': reviews})


@login_required
def add_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    # Check if order is delivered
    if order.status != 'delivered':
        return redirect('order_tracking', order_id=order_id)

    # Check if review already exists
    if Review.objects.filter(order=order).exists():
        return redirect('review_list')

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')

        Review.objects.create(
            customer=request.user,
            cook=order.cook,
            order=order,
            rating=rating,
            comment=comment
        )

        # Update cook average rating
        cook = order.cook
        all_reviews = Review.objects.filter(cook=cook)
        avg_rating = sum(r.rating for r in all_reviews) / all_reviews.count()
        cook.rating = round(avg_rating, 1)
        cook.save()

        return redirect('review_list')

    return render(request, 'reviews/add_review.html', {'order': order})