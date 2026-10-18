// Матеріалізація еквівалентних точних ваг з prepare_similarity.py.
// Виконувати після part2 та prepare_similarity.py, у спеціальній навчальній БД.
// @name drop_old_movie_projection
CALL gds.graph.drop('movieGraph',false) YIELD graphName RETURN graphName;
// @name drop_old_user_projection
CALL gds.graph.drop('userGraph',false) YIELD graphName RETURN graphName;
// @name clear_derived_edges
MATCH ()-[r:CO_RATED|SIMILAR]->() DELETE r;
// @name load_co_rated
CALL apoc.periodic.iterate(
  "LOAD CSV WITH HEADERS FROM 'file:///co_rated.csv' AS row RETURN row",
  "MATCH (a:Movie {movieId:toInteger(row.source)}),(b:Movie {movieId:toInteger(row.target)})
   MERGE (a)-[r:CO_RATED]->(b) SET r.weight=toInteger(row.weight)",
  {batchSize:1000,parallel:false}
) YIELD total,failedBatches,failedOperations,errorMessages
RETURN total,failedBatches,failedOperations,errorMessages;
// @name project_movies
CALL gds.graph.project('movieGraph','Movie',
 {CO_RATED:{orientation:'UNDIRECTED',properties:'weight'}})
YIELD graphName,nodeCount,relationshipCount RETURN graphName,nodeCount,relationshipCount;
// @name pagerank
CALL gds.pageRank.stream('movieGraph',
 {relationshipWeightProperty:'weight',maxIterations:100,tolerance:0.000001,concurrency:1})
YIELD nodeId,score
WITH gds.util.asNode(nodeId) AS m,score
RETURN m.movieId AS movieId,m.title AS title,score,
 COUNT { (m)<-[:RATED]-() } AS ratingCount
ORDER BY score DESC,movieId LIMIT 10;
// @name load_similarity
CALL apoc.periodic.iterate(
  "LOAD CSV WITH HEADERS FROM 'file:///similar.csv' AS row RETURN row",
  "MATCH (a:User {userId:toInteger(row.source)}),(b:User {userId:toInteger(row.target)})
   MERGE (a)-[r:SIMILAR]->(b)
   SET r.weight=toInteger(row.weight),r.distance=toFloat(row.distance)",
  {batchSize:1000,parallel:false}
) YIELD total,failedBatches,failedOperations,errorMessages
RETURN total,failedBatches,failedOperations,errorMessages;
// @name project_users
CALL gds.graph.project('userGraph','User',
 {SIMILAR:{orientation:'UNDIRECTED',properties:['weight','distance']}})
YIELD graphName,nodeCount,relationshipCount RETURN graphName,nodeCount,relationshipCount;
// @name louvain
CALL gds.louvain.write('userGraph',
 {relationshipWeightProperty:'weight',writeProperty:'community',concurrency:1})
YIELD communityCount,modularity,ranLevels,nodePropertiesWritten
RETURN communityCount,modularity,ranLevels,nodePropertiesWritten;
// @name community_sizes
MATCH (u:User)
RETURN u.community AS community,count(*) AS users
ORDER BY users DESC,community LIMIT 10;
// @name community_genres
MATCH (u:User)
WITH u.community AS community,count(*) AS communitySize
CALL {
 WITH community
 MATCH (u:User)-[r:RATED]->(:Movie)-[:HAS_GENRE]->(g:Genre)
 WHERE u.community=community AND r.rating>=4
 WITH g.name AS genre,count(*) AS highRatings
 ORDER BY highRatings DESC,genre LIMIT 3
 RETURN collect({genre:genre,highRatings:highRatings}) AS topGenres
}
RETURN community,communitySize,topGenres
ORDER BY communitySize DESC,community;
// @name isolated_users
MATCH (u:User)
RETURN count(*) AS users,
 sum(CASE WHEN COUNT { (u)-[:SIMILAR]-() }=0 THEN 1 ELSE 0 END) AS isolated;
// @name dijkstra_pairs
// Показові пари + 100 відтворюваних різних пар по всьому діапазону ID.
WITH [[1,2],[4169,1680],[4277,1941],[1181,889]] +
 [i IN range(0,99) | [1+((i*59)%6040),1+((i*97+1000)%6040)]] AS pairs
UNWIND pairs AS pair
MATCH (source:User {userId:pair[0]}),(target:User {userId:pair[1]})
CALL {
 WITH source,target
 CALL gds.shortestPath.dijkstra.stream('userGraph',
  {sourceNode:source,targetNode:target,relationshipWeightProperty:'distance'})
 YIELD totalCost,nodeIds
 RETURN collect({cost:totalCost,hops:size(nodeIds)-1,
                 users:[id IN nodeIds | gds.util.asNode(id).userId]}) AS paths
}
RETURN source.userId AS source,target.userId AS target,
 CASE WHEN size(paths)=0 THEN null ELSE paths[0].cost END AS cost,
 CASE WHEN size(paths)=0 THEN null ELSE paths[0].hops END AS hops,
 CASE WHEN size(paths)=0 THEN [] ELSE paths[0].users END AS users;
