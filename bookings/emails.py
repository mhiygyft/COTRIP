"""
Email notification system for booking-related events
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)


class BookingEmailService:
    """Service for sending booking-related emails"""
    
    @staticmethod
    def send_booking_confirmation(booking):
        """Send booking confirmation email to customer"""
        try:
            # Get current site
            current_site = Site.objects.get_current()
            
            # Email context
            context = {
                'booking': booking,
                'passenger': booking.passengers.first(),
                'site': current_site,
                'support_email': 'support@novaryo.com',
                'year': timezone.now().year
            }
            
            # Render email templates
            subject = f"Booking Confirmation - {booking.booking_reference}"
            text_content = render_to_string('bookings/emails/confirmation.txt', context)
            html_content = render_to_string('bookings/emails/confirmation.html', context)
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.contact_email],
                cc=[booking.user.email] if booking.user.email != booking.contact_email else [],
                reply_to=['support@novaryo.com']
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            logger.info(f"Booking confirmation email sent for {booking.booking_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send booking confirmation email for {booking.booking_reference}: {str(e)}")
            return False
    
    @staticmethod
    def send_booking_cancellation(booking, reason=None):
        """Send booking cancellation email to customer"""
        try:
            # Get current site
            current_site = Site.objects.get_current()
            
            # Email context
            context = {
                'booking': booking,
                'passenger': booking.passengers.first(),
                'reason': reason,
                'site': current_site,
                'support_email': 'support@novaryo.com',
                'year': timezone.now().year
            }
            
            # Render email templates
            subject = f"Booking Cancelled - {booking.booking_reference}"
            text_content = render_to_string('bookings/emails/cancellation.txt', context)
            html_content = render_to_string('bookings/emails/cancellation.html', context)
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.contact_email],
                cc=[booking.user.email] if booking.user.email != booking.contact_email else [],
                reply_to=['support@novaryo.com']
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            logger.info(f"Booking cancellation email sent for {booking.booking_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send booking cancellation email for {booking.booking_reference}: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_receipt(booking, payment):
        """Send payment receipt email to customer"""
        try:
            # Skip for skipped payments
            if payment.payment_method == 'skipped':
                return True
                
            # Get current site
            current_site = Site.objects.get_current()
            
            # Email context
            context = {
                'booking': booking,
                'payment': payment,
                'passenger': booking.passengers.first(),
                'site': current_site,
                'support_email': 'support@novaryo.com',
                'year': timezone.now().year
            }
            
            # Render email templates
            subject = f"Payment Receipt - {booking.booking_reference}"
            text_content = render_to_string('bookings/emails/payment_receipt.txt', context)
            html_content = render_to_string('bookings/emails/payment_receipt.html', context)
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.contact_email],
                cc=[booking.user.email] if booking.user.email != booking.contact_email else [],
                reply_to=['support@novaryo.com']
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            logger.info(f"Payment receipt email sent for {booking.booking_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment receipt email for {booking.booking_reference}: {str(e)}")
            return False
    
    @staticmethod
    def send_booking_reminder(booking, days_until_departure):
        """Send booking reminder email before departure"""
        try:
            # Get current site
            current_site = Site.objects.get_current()
            
            # Email context
            context = {
                'booking': booking,
                'passenger': booking.passengers.first(),
                'days_until_departure': days_until_departure,
                'site': current_site,
                'support_email': 'support@novaryo.com',
                'year': timezone.now().year
            }
            
            # Render email templates
            subject = f"Travel Reminder - {booking.booking_reference} departing in {days_until_departure} days"
            text_content = render_to_string('bookings/emails/reminder.txt', context)
            html_content = render_to_string('bookings/emails/reminder.html', context)
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.contact_email],
                cc=[booking.user.email] if booking.user.email != booking.contact_email else [],
                reply_to=['support@novaryo.com']
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            logger.info(f"Booking reminder email sent for {booking.booking_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send booking reminder email for {booking.booking_reference}: {str(e)}")
            return False


def send_booking_confirmation_email(booking):
    """Helper function to send booking confirmation email"""
    return BookingEmailService.send_booking_confirmation(booking)


def send_booking_cancellation_email(booking, reason=None):
    """Helper function to send booking cancellation email"""
    return BookingEmailService.send_booking_cancellation(booking, reason)


def send_payment_receipt_email(booking, payment):
    """Helper function to send payment receipt email"""
    return BookingEmailService.send_payment_receipt(booking, payment)


def send_booking_reminder_email(booking, days_until_departure):
    """Helper function to send booking reminder email"""
    return BookingEmailService.send_booking_reminder(booking, days_until_departure)