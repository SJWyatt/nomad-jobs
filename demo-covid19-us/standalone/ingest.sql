SET GLOBAL local_infile = 'ON';

CREATE TABLE bases( 
name varchar(255), 
state varchar(255), 
latitude float(10,6), 
longitude float(10,6)
);

-- Importing the csv file data in the tables createsLOAD DATA LOCAL 

LOAD DATA LOCAL INFILE '/home/ubuntu/sql/af_bases.csv' INTO TABLE bases 
FIELDS TERMINATED BY ',' ENCLOSED BY '' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;

-- SET GLOBAL local_infile = 'ON';

CREATE TABLE bases( 
name varchar(255), 
state varchar(255), 
geohash varchar(255),
confirmed float,
timestamp timestamp not null default current_timestamp on update current_timestamp
);

-- -- Importing the csv file data in the tables createsLOAD DATA LOCAL 

LOAD DATA LOCAL INFILE '/home/ubuntu/sql/af_bases.csv' INTO TABLE bases 
FIELDS TERMINATED BY ',' ENCLOSED BY '' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;

