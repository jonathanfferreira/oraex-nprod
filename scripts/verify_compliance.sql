-- Verify Compliance Parameters
SET LINESIZE 200
SET PAGESIZE 50

PROMPT === FORCE LOGGING ===
SELECT force_logging FROM v$database;

PROMPT === COMPLIANCE PARAMETERS ===
SELECT name, value FROM v$parameter WHERE name IN ('recyclebin','audit_trail','spfile');

PROMPT === TS_DATA TABLESPACE ===
SELECT tablespace_name, status FROM dba_tablespaces WHERE tablespace_name = 'TS_DATA';

PROMPT === DEFAULT PROFILE ===
SELECT resource_name, limit FROM dba_profiles WHERE profile = 'DEFAULT' AND resource_name IN ('PASSWORD_LIFE_TIME','FAILED_LOGIN_ATTEMPTS');

EXIT;
