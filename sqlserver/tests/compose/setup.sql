-- AdventureWorks databases
RESTORE DATABASE [AdventureWorks2017] FROM  DISK = N'/var/opt/mssql/backup/AdventureWorks2017.bak' WITH
FILE = 1,  MOVE N'AdventureWorks2017' TO N'/var/opt/mssql/data/AdventureWorks2017.mdf',
MOVE N'AdventureWorks2017_log' TO N'/var/opt/mssql/data/AdventureWorks2017_log.ldf',
REPLACE, NOUNLOAD,  STATS = 2;

-- Add example databases with non-standard names
CREATE DATABASE [1234_TEST];
CREATE DATABASE [TEST WITH SPACES]

-- datadog user
CREATE LOGIN datadog WITH PASSWORD = 'hey-there-datadog123';
CREATE USER datadog FOR LOGIN datadog;
GRANT SELECT on sys.dm_os_performance_counters to datadog;
GRANT VIEW SERVER STATE to datadog;
GRANT CONNECT ANY DATABASE to datadog;
GRANT VIEW ANY DEFINITION to datadog;

-- test users
CREATE LOGIN bob WITH PASSWORD = 'hey-there-bob123';
CREATE USER bob FOR LOGIN bob;
GRANT CONNECT ANY DATABASE to bob;

-- Create test database for integration tests
-- only bob has read/write access to this database
CREATE DATABASE DATADOG_TEST;
GO
USE DATADOG_TEST;
CREATE TABLE DATADOG_TEST.dbo.things (id int, name varchar(255));
INSERT INTO DATADOG_TEST.dbo.things VALUES (1, 'foo'), (2, 'bar');
CREATE USER bob FOR LOGIN bob;
GO

EXEC sp_addrolemember 'db_datareader', 'bob'
EXEC sp_addrolemember 'db_datawriter', 'bob'
