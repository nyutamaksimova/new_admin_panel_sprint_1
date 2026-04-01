import os
import sqlite3
from contextlib import closing
from dataclasses import fields
from datetime import datetime
from zoneinfo import ZoneInfo

import psycopg
from dotenv import load_dotenv
from psycopg import ClientCursor
from psycopg.rows import dict_row

from sqlite_to_postgres.models import FilmWork, Person, Genre, PersonFilmWork, GenreFilmWork

BATCH_SIZE = 500
MODELS = {'film_work': FilmWork,
          'person': Person,
          'genre': Genre,
          'person_film_work': PersonFilmWork,
          'genre_film_work': GenreFilmWork}
FIELD_MAPPING = {
    'created': 'created_at',
    'modified': 'updated_at'
}


def test_transfer():
    load_dotenv()

    dsl = {
        'dbname': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT'),
    }

    with sqlite3.connect('..\..\db.sqlite') as sqlite_conn, psycopg.connect(
            **dsl, row_factory=dict_row, cursor_factory=ClientCursor
    ) as pg_conn:
        sqlite_conn.row_factory = sqlite3.Row
        with closing(sqlite_conn.cursor()) as sqlite_cursor, closing(pg_conn.cursor(row_factory=dict_row)) as pg_cursor:
            for model, data_class in MODELS.items():
                model_fields = {f.name for f in fields(data_class)}
                sqlite_cursor.execute(f'SELECT * FROM {model}')

                while batch := sqlite_cursor.fetchmany(BATCH_SIZE):
                    original_batch = []

                    for record in batch:
                        row_dict = dict(record)
                        prepared = {}

                        for field in model_fields:
                            sqlite_field = FIELD_MAPPING.get(field, field)

                            if sqlite_field in {'created_at', 'updated_at'}:
                                prepared[field] = datetime.fromisoformat(row_dict[sqlite_field]).astimezone(
                                    ZoneInfo("Etc/UTC"))
                            elif sqlite_field in row_dict and row_dict[sqlite_field] is not None:
                                prepared[field] = row_dict[sqlite_field]
                            else:
                                prepared[field] = None

                        original_batch.append(data_class(**prepared))

                    ids = [element.id for element in original_batch]

                    pg_cursor.execute(f'SELECT * FROM content.{model} WHERE id = ANY(%s)', [ids])

                    transferred_batch = [data_class(**dict(record)) for record in pg_cursor.fetchall()]

                    assert len(original_batch) == len(transferred_batch)
                    assert original_batch == transferred_batch
