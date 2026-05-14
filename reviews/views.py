from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, TemplateView
from .models import Review, ReviewHelpful
from bookings.models import Booking
from django.db.models import Avg, Count

class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        return Review.objects.filter(is_approved=True).select_related('user', 'hotel', 'flight')

class ReviewDetailView(TemplateView):
    template_name = 'reviews/detail.html'

class WriteReviewView(TemplateView):
    template_name = 'reviews/write.html'

@login_required
def create_review(request, booking_id):
    """Create review for a completed booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check if review already exists
    if Review.objects.filter(user=request.user, booking=booking).exists():
        messages.error(request, 'You have already reviewed this booking.')
        return redirect('bookings:detail', booking_id=booking_id)
    
    if request.method == 'POST':
        # Simple review creation
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        
        if all([rating, title, comment]):
            review = Review.objects.create(
                user=request.user,
                booking=booking,
                flight=booking.flight if hasattr(booking, 'flight') else None,
                review_type='flight' if hasattr(booking, 'flight') else 'service',
                rating=int(rating),
                title=title,
                comment=comment
            )
            messages.success(request, 'Thank you for your review!')
            return redirect('bookings:detail', booking_id=booking_id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {'booking': booking}
    return render(request, 'reviews/write.html', context)

class ReviewAPIView(TemplateView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'Reviews API endpoint'})
