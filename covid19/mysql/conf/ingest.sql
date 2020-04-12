CREATE DATABASE geolocations;
USE geolocations;

CREATE TABLE bases( 
name varchar(255), 
state varchar(255), 
geohash varchar(255),
confirmed float,
timestamp timestamp not null default current_timestamp on update current_timestamp
);

LOAD DATA LOCAL INFILE '/local/data/af_bases.csv' INTO TABLE bases 
FIELDS TERMINATED BY ',' ENCLOSED BY '' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;
