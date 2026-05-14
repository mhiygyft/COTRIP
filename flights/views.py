from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.http import JsonResponse
from django.urls import reverse
from urllib.parse import urlencode
from django.utils import timezone
from datetime import datetime, time, timedelta
from decimal import Decimal

from .models import Flight, Airport, Airline, Route, FlightSearch
from .forms import FlightSearchForm, FlightFilterForm, FlightSearchSaveForm, QuickFlightSearchForm


def flight_search(request):
    """Main flight search page"""
    form = FlightSearchForm(request.GET or None)
    airports = Airport.objects.filter(is_popular=True).order_by('name')
    
    context = {
        'form': form,
        'airports': airports,
        'page_title': 'Search Flights'
    }
    
    if form.is_valid():
        # Redirect to results with search parameters
        params = {
            'origin': form.cleaned_data['origin'].id,
            'destination': form.cleaned_data['destination'].id,
            'departure_date': form.cleaned_data['departure_date'].strftime('%Y-%m-%d'),
            'trip_type': form.cleaned_data['trip_type'],
            'passengers': form.cleaned_data['passengers'],
            'cabin_class': form.cleaned_data['cabin_class'],
        }
        
        if form.cleaned_data.get('return_date'):
            params['return_date'] = form.cleaned_data['return_date'].strftime('%Y-%m-%d')
        
        return redirect(f"{reverse('flights:search_results')}?{urlencode(params)}")
    
    return render(request, 'flights/search.html', context)


def flight_search_results(request):
    """Flight search results with filtering and sorting"""
    # Get search parameters from URL or form
    origin_id = request.GET.get('origin')
    destination_id = request.GET.get('destination')
    departure_date = request.GET.get('departure_date')
    return_date = request.GET.get('return_date')
    trip_type = request.GET.get('trip_type', 'one_way')
    passengers = int(request.GET.get('passengers', 1))
    cabin_class = request.GET.get('cabin_class', 'economy')
    
    # Validate required parameters
    if not all([origin_id, destination_id, departure_date]):
        messages.error(request, 'Please provide all required search parameters.')
        return redirect('flights:search')
    
    try:
        origin = Airport.objects.get(id=origin_id)
        destination = Airport.objects.get(id=destination_id)
        dep_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
        ret_date = None
        if return_date:
            ret_date = datetime.strptime(return_date, '%Y-%m-%d').date()
    except (Airport.DoesNotExist, ValueError):
        messages.error(request, 'Invalid search parameters.')
        return redirect('flights:search')
    
    # Base flight query for outbound flights
    outbound_flights = Flight.objects.filter(
        origin=origin,
        destination=destination,
        departure_time__date=dep_date
    ).select_related('airline', 'aircraft', 'origin', 'destination')
    
    # Filter by availability based on cabin class
    availability_field = f'{cabin_class}_available'
    price_field = f'{cabin_class}_price'
    
    # Ensure flights have availability and pricing for selected class
    filter_kwargs = {
        f'{availability_field}__gte': passengers,
        f'{price_field}__isnull': False
    }
    outbound_flights = outbound_flights.filter(**filter_kwargs)
    
    # Return flights for round trip
    return_flights = []
    if trip_type == 'round_trip' and ret_date:
        return_flights = Flight.objects.filter(
            origin=destination,
            destination=origin,
            departure_time__date=ret_date,
            **filter_kwargs
        ).select_related('airline', 'aircraft', 'origin', 'destination')
    
    # Get airlines for filter form
    airlines_in_results = Airline.objects.filter(
        id__in=outbound_flights.values_list('airline_id', flat=True)
    ).order_by('name')
    
    # Apply filters
    filter_form = FlightFilterForm(request.GET, airlines_queryset=airlines_in_results)
    
    if filter_form.is_valid():
        outbound_flights = apply_flight_filters(outbound_flights, filter_form.cleaned_data, cabin_class)
        if return_flights:
            return_flights = apply_flight_filters(return_flights, filter_form.cleaned_data, cabin_class)
    
    # Sort flights
    sort_by = request.GET.get('sort_by', 'price_low_high')
    outbound_flights = sort_flights(outbound_flights, sort_by, cabin_class)
    if return_flights:
        return_flights = sort_flights(return_flights, sort_by, cabin_class)
    
    # Pagination for outbound flights
    paginator = Paginator(outbound_flights, 10)
    page_number = request.GET.get('page')
    outbound_page = paginator.get_page(page_number)
    
    # Calculate price range for filters
    price_range = outbound_flights.aggregate(
        min_price=Min(price_field),
        max_price=Max(price_field)
    )
    
    # Save search for logged-in users
    save_form = None
    if request.user.is_authenticated:
        save_form = FlightSearchSaveForm(user=request.user)
        
        if request.method == 'POST' and 'save_search' in request.POST:
            save_form = FlightSearchSaveForm(request.POST, user=request.user)
            if save_form.is_valid():
                search = save_form.save(commit=False)
                search.origin = origin
                search.destination = destination
                search.departure_date = dep_date
                search.return_date = ret_date
                search.passengers = passengers
                search.cabin_class = cabin_class
                search.trip_type = trip_type
                search.save()
                messages.success(request, f'Search saved as "{search.search_name}"')
    
    context = {
        'outbound_flights': outbound_page,
        'return_flights': return_flights[:5] if return_flights else [],  # Show top 5 return flights
        'origin': origin,
        'destination': destination,
        'departure_date': dep_date,
        'return_date': ret_date,
        'trip_type': trip_type,
        'passengers': passengers,
        'cabin_class': cabin_class,
        'filter_form': filter_form,
        'save_form': save_form,
        'price_range': price_range,
        'sort_by': sort_by,
        'page_title': f'Flights from {origin.city} to {destination.city}'
    }
    
    return render(request, 'flights/search_results.html', context)


def apply_flight_filters(queryset, filters, cabin_class):
    """Apply various filters to flight queryset"""
    
    if filters.get('airlines'):
        queryset = queryset.filter(airline__in=filters['airlines'])
    
    if filters.get('stops') == '0':
        queryset = queryset.filter(stops=0)
    elif filters.get('stops') == '1':
        queryset = queryset.filter(stops=1)
    elif filters.get('stops') == '2+':
        queryset = queryset.filter(stops__gte=2)
    
    # Time filters
    if filters.get('departure_time'):
        time_ranges = {
            'morning': (time(6, 0), time(12, 0)),
            'afternoon': (time(12, 0), time(18, 0)),
            'evening': (time(18, 0), time(23, 59)),
            'late_night': (time(0, 0), time(6, 0)),
        }
        if filters['departure_time'] in time_ranges:
            start_time, end_time = time_ranges[filters['departure_time']]
            queryset = queryset.filter(
                departure_time__time__range=(start_time, end_time)
            )
    
    if filters.get('arrival_time'):
        time_ranges = {
            'morning': (time(6, 0), time(12, 0)),
            'afternoon': (time(12, 0), time(18, 0)),
            'evening': (time(18, 0), time(23, 59)),
            'late_night': (time(0, 0), time(6, 0)),
        }
        if filters['arrival_time'] in time_ranges:
            start_time, end_time = time_ranges[filters['arrival_time']]
            queryset = queryset.filter(
                arrival_time__time__range=(start_time, end_time)
            )
    
    # Price filters
    price_field = f'{cabin_class}_price'
    if filters.get('min_price'):
        queryset = queryset.filter(**{f'{price_field}__gte': filters['min_price']})
    
    if filters.get('max_price'):
        queryset = queryset.filter(**{f'{price_field}__lte': filters['max_price']})
    
    return queryset


def sort_flights(queryset, sort_by, cabin_class):
    """Sort flight queryset by specified criteria"""
    price_field = f'{cabin_class}_price'
    
    if sort_by == 'departure_time':
        return queryset.order_by('departure_time')
    elif sort_by == 'arrival_time':
        return queryset.order_by('arrival_time')
    elif sort_by == 'duration':
        return queryset.order_by('duration_minutes')
    elif sort_by == 'price_low_high':
        return queryset.order_by(price_field)
    elif sort_by == 'price_high_low':
        return queryset.order_by(f'-{price_field}')
    else:
        return queryset.order_by(price_field)  # Default sort


def flight_detail(request, flight_id):
    """Detailed view of a specific flight"""
    flight = get_object_or_404(
        Flight.objects.select_related('airline', 'aircraft', 'origin', 'destination', 'route'),
        id=flight_id
    )
    
    # Get baggage allowances for this airline
    baggage_allowances = flight.airline.baggageallowance_set.all().order_by('fare_type')
    
    # Check if user has saved this flight
    is_saved = False
    if request.user.is_authenticated:
        from users.models import SavedFlight
        is_saved = SavedFlight.objects.filter(user=request.user, flight=flight).exists()
    
    context = {
        'flight': flight,
        'baggage_allowances': baggage_allowances,
        'is_saved': is_saved,
        'page_title': f'{flight.airline.name} {flight.flight_number}'
    }
    
    return render(request, 'flights/flight_detail.html', context)


def airports_autocomplete(request):
    """AJAX endpoint for airport autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    airports = Airport.objects.filter(
        Q(name__icontains=query) |
        Q(city__icontains=query) |
        Q(iata_code__icontains=query)
    ).filter(is_popular=True)[:10]
    
    results = [
        {
            'id': airport.iata_code,
            'text': f'{airport.city} ({airport.iata_code}) - {airport.name}',
            'city': airport.city,
            'code': airport.iata_code
        }
        for airport in airports
    ]
    
    return JsonResponse({'results': results})


@login_required
def save_flight(request, flight_id):
    """Save or unsave a flight for the current user"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    flight = get_object_or_404(Flight, id=flight_id)
    
    from users.models import SavedFlight
    
    saved_flight, created = SavedFlight.objects.get_or_create(
        user=request.user,
        flight=flight
    )
    
    if not created:
        saved_flight.delete()
        is_saved = False
        message = 'Flight removed from saved flights'
    else:
        is_saved = True
        message = 'Flight saved successfully'
    
    return JsonResponse({
        'is_saved': is_saved,
        'message': message
    })


@login_required
def saved_searches(request):
    """Display user's saved flight searches"""
    searches = FlightSearch.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(searches, 10)
    page_number = request.GET.get('page')
    searches_page = paginator.get_page(page_number)
    
    context = {
        'searches': searches_page,
        'page_title': 'Saved Flight Searches'
    }
    
    return render(request, 'flights/saved_searches.html', context)


@login_required
def delete_saved_search(request, search_id):
    """Delete a saved flight search"""
    search = get_object_or_404(FlightSearch, id=search_id, user=request.user)
    
    if request.method == 'POST':
        search_name = search.search_name
        search.delete()
        messages.success(request, f'Deleted saved search "{search_name}"')
    
    return redirect('flights:saved_searches')


def quick_search_redirect(request):
    """Handle quick search form submissions and redirect to full search"""
    form = QuickFlightSearchForm(request.GET)
    
    if form.is_valid():
        params = {
            'origin': form.cleaned_data['origin'].id,
            'destination': form.cleaned_data['destination'].id,
            'departure_date': form.cleaned_data['departure_date'].strftime('%Y-%m-%d'),
            'trip_type': 'one_way',
            'passengers': 1,
            'cabin_class': 'economy',
        }
        return redirect(f"{reverse('flights:search_results')}?{urlencode(params)}")
    
    # If form is invalid, redirect to main search with error
    messages.error(request, 'Please correct the search parameters and try again.')
    return redirect('flights:search')
