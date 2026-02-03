-- Apply TS_DATA tablespace
CREATE TABLESPACE TS_DATA 
  DATAFILE '/u02/oracle/oradata/orcl/ts_data01.dbf' 
  SIZE 100M AUTOEXTEND ON NEXT 10M MAXSIZE 2G;

-- Verify
SELECT tablespace_name, status FROM dba_tablespaces WHERE tablespace_name = 'TS_DATA';

EXIT;
