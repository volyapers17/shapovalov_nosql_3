// @name degree_distribution
MATCH (n)
WITH labels(n)[0] AS label,COUNT { (n)-[:RATED|HAS_GENRE]-() } AS degree
RETURN label,count(*) AS nodes,min(degree) AS minimum,avg(degree) AS mean,
       percentileCont(degree,0.5) AS median,percentileCont(degree,0.95) AS p95,
       percentileCont(degree,0.99) AS p99,max(degree) AS maximum
ORDER BY label;
// @name top_degrees
MATCH (n)
WITH n,COUNT { (n)-[:RATED|HAS_GENRE]-() } AS degree
RETURN labels(n)[0] AS label,coalesce(n.title,n.name,toString(n.userId)) AS node,
       coalesce(n.movieId,n.userId) AS entityId,degree
ORDER BY degree DESC,label,node LIMIT 20;
// @name genre_degrees
MATCH (g:Genre)
RETURN g.name AS genre,COUNT { (g)<-[:HAS_GENRE]-() } AS degree
ORDER BY degree DESC,genre;
// @name top_users
MATCH (u:User)
RETURN u.userId AS userId,COUNT { (u)-[:RATED]->() } AS degree
ORDER BY degree DESC,userId LIMIT 10;
// @name movie_coverage
MATCH (m:Movie)
WITH COUNT { (m)<-[:RATED]-() } AS ratings
RETURN count(*) AS allMovies,sum(CASE WHEN ratings=0 THEN 1 ELSE 0 END) AS unratedMovies;
