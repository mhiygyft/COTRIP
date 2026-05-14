from django import forms
from django.core.exceptions import ValidationError
from .models import RewardRedemption, LoyaltyMembership


class RewardRedemptionForm(forms.ModelForm):
    """Form for redeeming rewards"""
    
    booking_reference = forms.CharField(
        max_length=10,
        required=False,
        help_text="Associate this redemption with a booking (optional)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., NV123456'
        })
    )
    
    notes = forms.CharField(
        required=False,
        help_text="Additional notes or special requests",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special instructions or requests...'
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="I accept the terms and conditions for reward redemption",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = RewardRedemption
        fields = ['booking_reference', 'notes']
    
    def clean_booking_reference(self):
        booking_reference = self.cleaned_data.get('booking_reference', '').strip().upper()
        
        if booking_reference and not booking_reference.startswith('NV'):
            raise ValidationError("Booking reference must start with 'NV'")
        
        if booking_reference and len(booking_reference) != 8:
            raise ValidationError("Booking reference must be 8 characters long (e.g., NV123456)")
        
        return booking_reference


class PointsFilterForm(forms.Form):
    """Form for filtering points history"""
    
    TRANSACTION_TYPE_CHOICES = [('', 'All Types')] + [
        (choice[0], choice[1]) for choice in RewardRedemption.STATUS_CHOICES
    ]
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To Date'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("From date cannot be after To date")
        
        return cleaned_data


class RewardsFilterForm(forms.Form):
    """Form for filtering rewards catalog"""
    
    CATEGORY_CHOICES = [('', 'All Categories')] + [
        (choice[0], choice[1]) for choice in RewardRedemption.STATUS_CHOICES
    ]
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    max_points = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum points'
        }),
        label='Max Points'
    )
    
    available_only = forms.BooleanField(
        required=False,
        initial=False,
        label='Show only rewards I can redeem',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class ContactForm(forms.Form):
    """General contact form for loyalty program inquiries"""
    
    INQUIRY_TYPES = [
        ('general', 'General Inquiry'),
        ('points', 'Points Balance Question'),
        ('redemption', 'Reward Redemption Issue'),
        ('tier', 'Tier Status Question'),
        ('technical', 'Technical Support'),
        ('other', 'Other'),
    ]
    
    inquiry_type = forms.ChoiceField(
        choices=INQUIRY_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Type of Inquiry'
    )
    
    subject = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of your inquiry'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Please provide details about your inquiry...'
        }),
        min_length=10,
        help_text="Please provide at least 10 characters"
    )
    
    member_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your loyalty member ID (optional)'
        }),
        help_text="Your NV member ID if available"
    )
    
    def clean_member_id(self):
        member_id = self.cleaned_data.get('member_id', '').strip().upper()
        
        if member_id:
            if not member_id.startswith('NV'):
                raise ValidationError("Member ID must start with 'NV'")
            
            if len(member_id) != 10:
                raise ValidationError("Member ID must be 10 characters long")
            
            # Verify member exists
            try:
                LoyaltyMembership.objects.get(member_id=member_id)
            except LoyaltyMembership.DoesNotExist:
                raise ValidationError("Member ID not found in our system")
        
        return member_id