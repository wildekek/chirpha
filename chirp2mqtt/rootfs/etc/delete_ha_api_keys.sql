-- change to chirpstack database
\c chirpstack

-- delete already used HA api keys
DELETE FROM api_key WHERE name = 'chirpha';

-- exit psql
\q
