from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import PaymentTransaction


@login_required
def payment_history(request):
    transactions = PaymentTransaction.objects.filter(user=request.user).select_related("booking")
    return render(request, "payments/history.html", {
        "transactions": transactions,
        "page_title": "Payment History",
    })

