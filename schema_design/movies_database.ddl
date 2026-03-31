CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.film_work (
    id uuid PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creation_date DATE,
    rating FLOAT,
    type VARCHAR(10) NOT NULL,
    created timestamp with time zone NOT NULL DEFAULT now(),
    modified timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content.genre (
    id uuid PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created timestamp with time zone NOT NULL DEFAULT now(),
    modified timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id uuid PRIMARY KEY,
    genre_id uuid NOT NULL REFERENCES content.genre (id) ON DELETE CASCADE,
    film_work_id uuid NOT NULL REFERENCES content.film_work (id) ON DELETE CASCADE,
    created timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content.person (
    id uuid PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    created timestamp with time zone NOT NULL DEFAULT now(),
    modified timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id uuid PRIMARY KEY,
	person_id uuid NOT NULL REFERENCES content.person (id) ON DELETE CASCADE,
    film_work_id uuid NOT NULL REFERENCES content.film_work (id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    created timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX film_work_date_rating_idx ON content.film_work(creation_date, rating);

CREATE INDEX film_work_title_idx ON content.film_work(title);

CREATE UNIQUE INDEX film_work_genre_idx ON content.genre_film_work(film_work_id, genre_id);

CREATE INDEX person_full_name_idx ON content.person(full_name);

CREATE UNIQUE INDEX film_work_person_role_idx ON content.person_film_work(film_work_id, person_id, role);

