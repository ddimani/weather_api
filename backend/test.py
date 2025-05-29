import json
from unittest.mock import patch

from django.http import JsonResponse
from django.urls import reverse
from django.test import TestCase, Client

from weather.models import City


class WeatherAppTests(TestCase):

    def setUp(self):
        self.client = Client()

    @patch('weather.views.get_weather_data')
    def test_index_view_with_invalid_city(self, mock_get_weather_data):
        """Тест отображения страницы с невалидным городом."""
        mock_get_weather_data.return_value = (None, 'Город не найден')
        response = self.client.post(reverse('index'), {'city': 'InvalidCity'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Город не найден')

    def test_autocomplete_view_with_query(self):
        """Проверяет корректность работы автозаполнения с запросом."""
        response = self.client.get(reverse('autocomplete'), {'q': 'Moscow'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = json.loads(response.content)
        self.assertIsInstance(data, list)

    def test_autocomplete_view_without_query(self):
        """Проверяет поведение автозаполнения при отсутствии запроса."""
        response = self.client.get(reverse('autocomplete'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = json.loads(response.content)
        self.assertEqual(data, [])

    def test_city_popularity_view(self):
        """Проверяет корректность работы endpoint популярных городов."""
        cities = (
            City.objects.all()
            .order_by('-search_count')
            .values('name', 'search_count')
        )
        city_list = list(cities)
        return JsonResponse(city_list, safe=False)
