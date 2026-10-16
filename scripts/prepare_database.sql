\set ON_ERROR_STOP on
\getenv app_user ACADEMY_APP_USER
\getenv app_password ACADEMY_APP_PASSWORD
SELECT :'app_user' <> current_user AS separate_role \gset
\if :separate_role
\else
  \echo 'The application role must differ from the maintenance role.'
  \quit 1
\endif
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L', :'app_user', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'app_user') \gexec
ALTER ROLE :"app_user" NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
SELECT format('GRANT CONNECT, CREATE ON DATABASE %I TO %I', current_database(), :'app_user') \gexec
ALTER SCHEMA public OWNER TO :"app_user";
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
-- Existing academy objects retain rows/constraints while their writer gets DDL ownership.
SELECT format('ALTER TABLE public.%I OWNER TO %I', tablename, :'app_user') FROM pg_tables WHERE schemaname = 'public' \gexec
SELECT format('ALTER SEQUENCE public.%I OWNER TO %I', sequencename, :'app_user') FROM pg_sequences WHERE schemaname = 'public' \gexec
