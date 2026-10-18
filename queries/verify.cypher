// @name versions
CALL dbms.components() YIELD name,versions,edition
RETURN name,versions,edition,apoc.version() AS apoc,gds.version() AS gds;
// @name indexes
SHOW INDEXES YIELD name,state,type,labelsOrTypes,properties
RETURN name,state,type,labelsOrTypes,properties ORDER BY name;
// @name duplicate_ratings
MATCH (u:User)-[r:RATED]->(m:Movie)
WITH u,m,count(r) AS copies WHERE copies>1
RETURN count(*) AS duplicatePairs;
// @name invalid_ratings
MATCH (u)-[r:RATED]->(m)
WHERE NOT u:User OR NOT m:Movie OR r.rating IS NULL OR r.timestamp IS NULL
 OR NOT r.rating IN [1,2,3,4,5] OR r.timestamp<0
RETURN count(*) AS invalid;
// @name database_rating_distribution
MATCH ()-[r:RATED]->()
RETURN r.rating AS rating,count(*) AS count ORDER BY rating;
// @name minimum_user_ratings
MATCH (u:User)
RETURN min(COUNT { (u)-[:RATED]->() }) AS minimum;
// @name similarity_sample_check
MATCH (a:User)-[s:SIMILAR]->(b:User)
WITH a,b,s ORDER BY a.userId,b.userId LIMIT 20
MATCH (a)-[r1:RATED]->(m:Movie)<-[r2:RATED]-(b)
WHERE r1.rating>=4 AND r2.rating>=4
WITH a,b,s,count(m) AS expected
RETURN a.userId AS source,b.userId AS target,s.weight AS actual,expected,s.weight=expected AS correct;
