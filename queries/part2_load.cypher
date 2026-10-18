// @name unique_users
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE;
// @name unique_movies
CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) REQUIRE m.movieId IS UNIQUE;
// @name unique_genres
CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE;
// @name await_indexes
CALL db.awaitIndexes(300);
// @name load_users
CALL apoc.periodic.iterate(
  "LOAD CSV WITH HEADERS FROM 'file:///users.csv' AS row RETURN row",
  "MERGE (u:User {userId:toInteger(row.userId)})
   SET u.gender=row.gender, u.age=toInteger(row.age), u.occupation=toInteger(row.occupation)",
  {batchSize:1000, parallel:false}
) YIELD batches,total,failedBatches,failedOperations,errorMessages
RETURN batches,total,failedBatches,failedOperations,errorMessages;
// @name load_movies
CALL apoc.periodic.iterate(
  "LOAD CSV WITH HEADERS FROM 'file:///movies.csv' AS row RETURN row",
  "MERGE (m:Movie {movieId:toInteger(row.movieId)})
   SET m.title=row.title, m.year=toInteger(row.year)
   WITH m,row UNWIND split(row.genres,'|') AS genre
   MERGE (g:Genre {name:genre}) MERGE (m)-[:HAS_GENRE]->(g)",
  {batchSize:500, parallel:false}
) YIELD batches,total,failedBatches,failedOperations,errorMessages
RETURN batches,total,failedBatches,failedOperations,errorMessages;
// @name load_ratings
CALL apoc.periodic.iterate(
  "LOAD CSV WITH HEADERS FROM 'file:///ratings.csv' AS row RETURN row",
  "MATCH (u:User {userId:toInteger(row.userId)})
   MATCH (m:Movie {movieId:toInteger(row.movieId)})
   MERGE (u)-[r:RATED]->(m)
   SET r.rating=toInteger(row.rating), r.timestamp=toInteger(row.timestamp)",
  {batchSize:5000, parallel:false}
) YIELD batches,total,failedBatches,failedOperations,errorMessages
RETURN batches,total,failedBatches,failedOperations,errorMessages;
// @name counts
CALL { MATCH (u:User) RETURN count(u) AS users }
CALL { MATCH (m:Movie) RETURN count(m) AS movies }
CALL { MATCH (g:Genre) RETURN count(g) AS genres }
CALL { MATCH ()-[r:RATED]->() RETURN count(r) AS ratings }
CALL { MATCH ()-[r:HAS_GENRE]->() RETURN count(r) AS hasGenre }
RETURN users,movies,genres,ratings,hasGenre;
