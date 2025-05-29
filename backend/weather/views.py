import requests
import json

from django.http import JsonResponse
from django.shortcuts import render

from core.constants import GEOCODE_API_URL, URL_OPEN_METEO
from weather.forms import CityForm
from weather.models import City


def index(request):
    """Отображает страницу поиска погоды и обрабатывает запросы."""
    form = CityForm(request.POST or None)
    weather_data = None
    search_history = request.COOKIES.get('search_history', '[]')
    try:
        search_history = json.loads(search_history)
    except json.JSONDecodeError:
        search_history = []

    city_name_from_history = request.GET.get('city', None)
    city_name_to_display = None

    if request.method == 'POST' or city_name_from_history:
        if request.method == 'POST':
            if form.is_valid():
                city_name = form.cleaned_data['city']
                city_name_to_display = city_name
            else:
                city_name = None
        else:
            city_name = city_name_from_history
            city_name_to_display = city_name

        if city_name:
            geocode_url = f'{GEOCODE_API_URL}{city_name}&count=1&language=ru'
            try:
                geocode_response = requests.get(geocode_url)
                geocode_response.raise_for_status()
                geocode_data = geocode_response.json()
                if geocode_data.get('results'):
                    latitude = geocode_data['results'][0]['latitude']
                    longitude = geocode_data['results'][0]['longitude']
                    city, created = City.objects.get_or_create(
                        name=city_name,
                        defaults={'latitude': latitude, 'longitude': longitude}
                    )
                    if not created:
                        city.search_count += 1
                        city.save()
                    else:
                        city.search_count = 1
                        city.save()

                    weather_data = get_weather_data(latitude, longitude)

                    if request.method == 'POST':
                        if city_name not in search_history:
                            search_history.insert(0, city_name)
                            search_history = search_history[:5]

                else:
                    weather_data = {'error': 'Город не найден!'}

            except requests.exceptions.RequestException as e:
                print(f'Ошибка при запросе к API: {e}')
                weather_data = {'error': 'Ошибка при получении данных'}
        else:
            weather_data = {'error': 'Некорректное название города'}
            city_name_to_display = None

        response = render(request, 'weather/index.html', {
            'form': form,
            'weather_data': weather_data,
            'search_history': search_history,
            'city_name': city_name_to_display
        })
        response.set_cookie('search_history', json.dumps(search_history))
        return response

    return render(request, 'weather/index.html', {
        'form': form,
        'weather_data': weather_data,
        'search_history': search_history,
        'city_name': city_name_to_display
    })


def get_weather_data(latitude, longitude):
    """Получает данные о погоде по координатам, используя API Open-Meteo."""
    url = (
        f'{URL_OPEN_METEO}?latitude={latitude}'
        f'&longitude={longitude}&current=temperature_2m,rain,'
        f'wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,'
        f'precipitation_probability_max&timezone=Europe/Moscow'
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        current = data.get('current', {})
        daily = data.get('daily', {})
        weather_data = {
            'temperature': current.get('temperature_2m'),
            'wind_speed': current.get('wind_speed_10m'),
            'max_temp': daily.get('temperature_2m_max', [None])[0],
            'min_temp': daily.get('temperature_2m_min', [None])[0],
            'precipitation_probability_max':
                daily.get('precipitation_probability_max', [None])[0],
        }
        return weather_data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return None


def autocomplete(request):
    """
    Предоставляет автозаполнение для названий городов.
    """
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse([], safe=False)

    geocode_url = f'{GEOCODE_API_URL}{query}&count=10&language=ru'
    try:
        response = requests.get(geocode_url)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])

        suggestions = []
        for result in results:
            suggestions.append({
                'name': result['name'],
                'latitude': result['latitude'],
                'longitude': result['longitude'],
                'country': result['country']
            })

        return JsonResponse(suggestions, safe=False)

    except requests.exceptions.RequestException as e:
        print(f'Ошибка при запросе к API геокодирования: {e}')
        return JsonResponse([], safe=False)


def city_popularity_view(request):
    """
    Представление для отображения списка городов и частоту запросов в HTML.
    """
    cities = City.objects.all().order_by('-search_count')
    return render(request, 'weather/city_popularity.html', {'cities': cities})
