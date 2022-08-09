 Postgresql settings for DHIS2

# Adjust depending on number of DHIS2 instances and their pool size
# By default each instance requires up to 80 connections
# This might be different if you have set pool in dhis.conf
max_connections = 200

# Tune these according to your environment
# About 25% available RAM for postgres
# shared_buffers = 3GB

# Multiply by max_connections to know potentially how much RAM is required
# work_mem=20MB

# As much as you can reasonably afford.  Helps with index generation
# during the analytics generation task
# maintenance_work_mem=512MB

# Approx 80% of (Available RAM - maintenance_work_mem - max_connections*work_mem)
# effective_cache_size=8GB

# This setting is suitable for good SSD disk.  For slower spinning disk consider
# changing to 4
random_page_cost = 1.1

checkpoint_completion_target = 0.8
synchronous_commit = off
log_min_duration_statement = 300s
max_locks_per_transaction = 1024
/etc/hosts
