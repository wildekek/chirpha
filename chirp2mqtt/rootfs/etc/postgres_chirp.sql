-- create role for authentication
create role chirpstack with login password 'chirpstack';

-- create database
create database chirpstack with owner chirpstack;

-- change to chirpstack database
\c chirpstack

-- create pg_trgm extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- exit psql
\q
