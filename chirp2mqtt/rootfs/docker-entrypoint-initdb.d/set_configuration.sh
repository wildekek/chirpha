#!/usr/bin/env bash
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '127.0.0.1'/" $PGDATA/postgresql.conf
sed -i -e '/IPv4 local connections/ {' -e 'n; s|.*|host    all             all             127.0.0.1/32            trust|' -e '}' $PGDATA/pg_hba.conf
sed -i -e '/IPv6 local connections/ {' -e 'n; s|.*|#host   all             all             ::1/128                 trust|' -e '}' $PGDATA/pg_hba.conf
sed -i "s/local   replication/#local   replication/" $PGDATA/pg_hba.conf
sed -i "s/local   replication/#local   replication/" $PGDATA/pg_hba.conf
sed -i "s/host    replication/#host    replication/" $PGDATA/pg_hba.conf
sed -i "s/.*log_checkpoints = .*/log_checkpoints = off/" $PGDATA/postgresql.conf
