import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass, fields, astuple
from datetime import date, datetime
from typing import Generator
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from psycopg import ClientCursor, connection as _connection
from psycopg.rows import dict_row


@dataclass
class FilmWork:
    id: UUID
    title: str
    description: str
    creation_date: date
    rating: float
    type: str
    created: datetime
    modified: datetime

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)


@dataclass
class Person:
    id: UUID
    full_name: str
    created: datetime
    modified: datetime

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)


@dataclass
class Genre:
    id: UUID
    name: str
    description: str
    created: datetime
    modified: datetime

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)


@dataclass
class GenreFilmWork:
    id: UUID
    genre_id: UUID
    film_work_id: UUID
    created: datetime

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)

        if isinstance(self.genre_id, str):
            self.genre_id = UUID(self.genre_id)

        if isinstance(self.film_work_id, str):
            self.film_work_id = UUID(self.film_work_id)


@dataclass
class PersonFilmWork:
    id: UUID
    person_id: UUID
    film_work_id: UUID
    role: str
    created: datetime

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)

        if isinstance(self.person_id, str):
            self.person_id = UUID(self.person_id)

        if isinstance(self.film_work_id, str):
            self.film_work_id = UUID(self.film_work_id)


BATCH_SIZE = 500
TABLES = ('film_work', 'person', 'genre', 'person_film_work', 'genre_film_work',)
MODELS = {'film_work': (FilmWork, 'id'),
          'person': (Person, 'id'),
          'genre': (Genre, 'id'),
          'person_film_work': (PersonFilmWork, 'person_id, film_work_id, role'),
          'genre_film_work': (GenreFilmWork, 'genre_id, film_work_id')}

FIELD_MAPPING = {
    'created': 'created_at',
    'modified': 'updated_at'
}

DEFAULTS = {
    'created': datetime.now,
    'modified': datetime.now,
}


def extract_data(sqlite_cursor: sqlite3.Cursor, table) -> Generator[list[sqlite3.Row], None, None]:
    sqlite_cursor.execute(f'SELECT * FROM {table}')
    while results := sqlite_cursor.fetchmany(BATCH_SIZE):
        yield results


def transform_data(sqlite_cursor: sqlite3.Cursor, table):
    model = MODELS[table][0]
    model_fields = {f.name for f in fields(model)}

    for batch in extract_data(sqlite_cursor, table):
        result = []

        for record in batch:
            row_dict = dict(record)
            prepared = {}

            for field in model_fields:
                sqlite_field = FIELD_MAPPING.get(field, field)

                if sqlite_field in row_dict and row_dict[sqlite_field] is not None:
                    prepared[field] = row_dict[sqlite_field]
                elif field in DEFAULTS:
                    prepared[field] = DEFAULTS[field]()
                else:
                    prepared[field] = None

            result.append(model(**prepared))
        yield result


class SQLiteLoader:
    """Загрузчик данных из таблиц SQLite"""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def load_movies(self, ) -> dict[str, list]:
        result = {'film_work': [], 'person': [], 'genre': [], 'person_film_work': [], 'genre_film_work': []}

        with closing(self.connection.cursor()) as sqlite_cur:
            for table in TABLES:
                result[table].extend(transform_data(sqlite_cur, table))

        return result


def batch_generator(data, batch_size=BATCH_SIZE):
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


class PostgresSaver:
    """Загрузчик данных в таблицы Postgres"""
    def __init__(self, pg_conn: _connection):
        self.pg_conn = pg_conn

    def save_all_data(self, data: dict):
        with closing(pg_conn.cursor(row_factory=dict_row)) as pg_cur:
            for table, records in data.items():
                model, index_columns = MODELS[table]
                column_names = [f.name for f in fields(model)]
                column_names_str = ','.join(column_names)

                col_count = ', '.join(['%s'] * len(column_names))
                for batch in records:
                    bind_values = ','.join(pg_cur.mogrify(f"({col_count})", astuple(element)) for element in batch)
                    query = (f'INSERT INTO content.{table} ({column_names_str}) VALUES {bind_values} '
                             f'ON CONFLICT ({index_columns}) DO NOTHING')
                    pg_cur.execute(query)

            pg_conn.commit()


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)

    data = sqlite_loader.load_movies()
    postgres_saver.save_all_data(data)


if __name__ == '__main__':
    load_dotenv()

    dsl = {
        'dbname': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT'),
    }

    with sqlite3.connect('db.sqlite') as sqlite_conn, psycopg.connect(
            **dsl, row_factory=dict_row, cursor_factory=ClientCursor
    ) as pg_conn:
        sqlite_conn.row_factory = sqlite3.Row
        load_from_sqlite(sqlite_conn, pg_conn)
