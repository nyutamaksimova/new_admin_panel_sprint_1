import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('name'), max_length=255, blank=False, unique=True)
    description = models.TextField(_('description'), blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'content\'.\'genre'
        verbose_name = _('genre')
        verbose_name_plural = _('genres')


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_('full_name'), max_length=255, blank=False)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'content\'.\'person'
        verbose_name = _('person')
        verbose_name_plural = _('people')

        indexes = [
            models.Index(
                fields=['full_name'],
                name='person_full_name_idx',
            ),
        ]


class FilmWork(UUIDMixin, TimeStampedMixin):
    class Type(models.TextChoices):
        MOVIE = 'movie'
        TV_SHOW = 'tv_show'

    title = models.CharField(_('title'), max_length=255, blank=False)
    description = models.TextField(_('description'), blank=True)
    creation_date = models.DateField(_('creation_date'), blank=True)
    rating = models.FloatField(_('rating'), blank=True, validators=[MinValueValidator(0),
                                                                    MaxValueValidator(100)])

    type = models.CharField(_('type'), max_length=10, choices=Type.choices)

    genres = models.ManyToManyField(Genre, through='GenreFilmWork')

    people = models.ManyToManyField(Person, through='PersonFilmWork')

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'content\'.\'film_work'
        verbose_name = _('film_work')
        verbose_name_plural = _('film_works')

        indexes = [
            models.Index(
                fields=['title'],
                name='film_work_title_idx',
            ),
            models.Index(
                fields=['creation_date', 'rating'],
                name='film_work_date_rating_idx',
            ),
        ]


class GenreFilmWork(UUIDMixin):
    film_work = models.ForeignKey('FilmWork', on_delete=models.CASCADE, verbose_name=_('film_work'))
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE, verbose_name=_('genre'))
    created = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        db_table = 'content\'.\'genre_film_work'

        constraints = [
            models.UniqueConstraint(
                fields=['film_work', 'genre'],
                name='film_work_genre_idx'
            )
        ]


class PersonFilmWork(UUIDMixin):
    class Role(models.TextChoices):
        ACTOR = 'actor'
        DIRECTOR = 'director'
        WRITER = 'writer'

    film_work = models.ForeignKey('FilmWork', on_delete=models.CASCADE, verbose_name=_('film_work'))
    person = models.ForeignKey('Person', on_delete=models.CASCADE, verbose_name=_('person'))
    role = models.CharField(_('role'), max_length=20, choices=Role.choices, blank=False)
    created = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        db_table = 'content\'.\'person_film_work'

        constraints = [
            models.UniqueConstraint(
                fields=['film_work', 'person'],
                name='film_work_person_idx'
            )
        ]
