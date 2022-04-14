CREATE
SOURCE sensors
FROM KAFKA BROKER 'redpanda:9092' TOPIC 'sensors'
FORMAT BYTES;


CREATE VIEW sensors_data AS
SELECT *
FROM (
         SELECT (data ->>'id')::int          AS id,
                (data ->>'pm25')::float      AS pm25,
                (data ->>'pm10')::float      AS pm10,
                (data ->>'geo_lat')::float   AS geo_lat,
                (data ->>'geo_lon')::float   AS geo_lon,
                (data ->>'timestamp')::float AS timestamp
         FROM (
                  SELECT CAST(data AS jsonb) AS data
                  FROM (
                           SELECT convert_from(data, 'utf8') AS data
                           FROM sensors
                       )
              )
     );

CREATE MATERIALIZED VIEW sensors_view AS
SELECT *
FROM sensors_data
WHERE mz_logical_timestamp() < (timestamp * 1000 + 100000)::numeric;


CREATE MATERIALIZED VIEW sensors_view_1s AS
SELECT *
FROM sensors_data
WHERE mz_logical_timestamp() < (timestamp * 1000 + 6000)::numeric;