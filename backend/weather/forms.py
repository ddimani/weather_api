from django import forms


class CityForm(forms.Form):
    """Форма для ввода названия города."""

    city = forms.CharField(
        label="Город",
        widget=forms.TextInput(attrs={'id': 'city_input'})
    )
