from django.db import models

from core.constants import MAX_LENGTH


class City(models.Model):
    """Модель для города."""

    name = models.CharField(
        max_length=MAX_LENGTH,
        unique=True,
        verbose_name='Название города',
        help_text='Введите название города'
    )
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')
    search_count = models.IntegerField(
        default=0, verbose_name='Количество поисков'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
