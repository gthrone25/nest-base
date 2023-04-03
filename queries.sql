-- get counts
select count(*) from gt-nest-thermo

-- get most recent records
select * from gt-nest-thermo order by measurement_ts DESC

-- get min/max temp and humidity
select max(ambient_humidity_pct) as maxhum, min(ambient_humidity_pct) as minhum, 
max(ambient_temp_cel) as maxtempc, min(ambient_temp_cel) as mintempc, max(ambient_temp_far) as maxtempf, min(ambient_temp_far) as mintempf
from gt-nest-thermo