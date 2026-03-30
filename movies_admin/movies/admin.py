from django.contrib import admin
from .models import Genre, FilmWork, GenreFilmWork, Person, PersonFilmWork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'description',)
    search_fields = ('name',)


class GenreFilmWorkInline(admin.TabularInline):
    model = GenreFilmWork


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    search_fields = ('full_name',)


class PersonFilmWorkInline(admin.TabularInline):
    model = PersonFilmWork


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmWorkInline, PersonFilmWorkInline)

    list_display = ('title', 'type', 'creation_date', 'rating',)

    list_filter = ('type', 'creation_date',)

    search_fields = ('title', 'description',)
