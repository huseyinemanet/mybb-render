# MyBB Backup Procedure

- Primary strategy: external PostgreSQL dumps plus a copy of operational secrets.
- Render Free local backup artifacts are not treated as durable backups.
- Database backup command:
  `PGPASSWORD='<password>' pg_dump -h <host> -U <user> -d <database> -f backup.sql`
- Required operational artifacts:
  `inc/config.php` values, Render environment secrets, ACP Basic Auth credentials, ACP secret PIN, active admin URL.
- Restore validation:
  restore the dump into a fresh PostgreSQL database, set matching env/config values, and verify forum home, user login, and ACP login.
