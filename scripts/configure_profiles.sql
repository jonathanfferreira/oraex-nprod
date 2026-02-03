-- =============================================================================
-- Script: configure_profiles.sql
-- Descrição: Configurações de Profiles e Parâmetros de Segurança (Getnet Standard)
-- =============================================================================

SET ECHO ON
SET FEEDBACK ON

-- 1. Criação de Profiles (Exemplo Getnet)
CREATE PROFILE APP_PROFILE LIMIT
  SESSIONS_PER_USER UNLIMITED
  CPU_PER_SESSION UNLIMITED
  CPU_PER_CALL UNLIMITED
  CONNECT_TIME 45
  IDLE_TIME 15
  LOGICAL_READS_PER_SESSION UNLIMITED
  LOGICAL_READS_PER_CALL UNLIMITED
  PRIVATE_SGA UNLIMITED
  COMPOSITE_LIMIT UNLIMITED
  PASSWORD_LIFE_TIME 90
  PASSWORD_GRACE_TIME 7
  PASSWORD_REUSE_MAX UNLIMITED
  PASSWORD_REUSE_TIME UNLIMITED
  PASSWORD_LOCK_TIME 1
  FAILED_LOGIN_ATTEMPTS 10;

-- 2. Ajuste do DEFAULT PROFILE
ALTER PROFILE DEFAULT LIMIT
  PASSWORD_LIFE_TIME UNLIMITED
  FAILED_LOGIN_ATTEMPTS 10;

-- 3. Parâmetros de Conformidade (Checks)
ALTER SYSTEM SET recyclebin='OFF' SCOPE=SPFILE;
ALTER SYSTEM SET audit_trail='DB' SCOPE=SPFILE;
-- Force Logging é operação de banco, não parametro spfile apenas
ALTER DATABASE FORCE LOGGING;

-- 4. Criação de Tablespaces Padrão (Exemplo)
CREATE TABLESPACE TS_DATA 
  DATAFILE '/u02/oracle/oradata/orcl/ts_data01.dbf' SIZE 100M AUTOEXTEND ON NEXT 10M MAXSIZE 2G;

EXIT;
