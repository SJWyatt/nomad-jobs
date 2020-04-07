 SET GLOBAL local_infile = 'ON';

CREATE TABLE province( 
data date, 
stato varchar(64), 
codice_regione int, 
denominazione_regione varchar(64), 
codice_provincia varchar(64), 
denominazione_provincia varchar(64), 
sigla_provincia varchar(2), 
latitude float, 
longitude float, 
totale_casi int
);

-- Importing the csv file data in the tables createsLOAD DATA LOCAL 

LOAD DATA LOCAL INFILE '/var/lib/mysql-files/dpc-covid19-ita-province.csv' INTO TABLE province 
FIELDS TERMINATED BY ',' ENCLOSED BY '' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;
