#!/usr/bin/env python3

import psycopg2
DBS = "training","dhis2"
TIMEOUT ="120 seconds"
PATTERN = "^SELECT TEI.uid|select count.*from analytics_"

dsn = "host={} dbname={} user={} password={}".format('172.19.2.20', 'postgres', 'postgres', 'password_here')
conn = psycopg2.connect(dsn)
# define your query string 
LONG_QUERIES=f"SELECT pid,now()-query_start as time,query from pg_stat_activity WHERE state != 'idle' AND query ~ '{PATTERN}' AND datname in {DBS} AND now()-query_start > '{TIMEOUT}'"
cur = conn.cursor()
cur.execute(LONG_QUERIES)
for row in  cur.fetchall():
    _pid = row[0]
    # Kill the long query here 
    cur.execute(f"SELECT pg_terminate_backend({_pid})")
