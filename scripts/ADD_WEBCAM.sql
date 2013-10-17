insert into webcams(id, ip, name, pan0, online, port, network, geom,
iservice, iserviceurl, sts, ets, county, hosted, hostedurl, sponsor,
sponsorurl, removed, state, moviebase, scrape_url, is_vapix) values ('KCRG-022', 'x.x.x.x',
'Manchester', 0, 't', 80, 'KCRG',
'SRID=4326;POINT(-91.4577 42.4841)', null, null,
'2013-09-27 12:00', null, 'Delaware', null, null, null, null, 'f', 'IA','manchester',
null, 't');

insert into webcam_scheduler select 'KCRG-022', begints, endts, is_daily,
replace(filename, 'ames', 'manchester'), movie_seconds
from webcam_scheduler WHERE cid = 'KCCI-016';

