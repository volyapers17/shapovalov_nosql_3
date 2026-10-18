// @name q1_thrillers
// Усі Thriller із середнім рейтингом строго > 4.0, без прихованого LIMIT.
MATCH (m:Movie)-[:HAS_GENRE]->(:Genre {name:'Thriller'})
MATCH (:User)-[r:RATED]->(m)
WITH m,avg(r.rating) AS averageRating,count(r) AS ratingCount
WHERE averageRating > 4.0
RETURN m.movieId AS movieId,m.title AS title,averageRating,ratingCount
ORDER BY averageRating DESC,ratingCount DESC,movieId;
// @name q2_five_star_users
MATCH (u:User)-[r:RATED]->(m:Movie)
WHERE r.rating=5
WITH u,count(DISTINCT m) AS fiveStarMovies
WHERE fiveStarMovies > 50
RETURN u.userId AS userId,fiveStarMovies
ORDER BY fiveStarMovies DESC,userId;
// @name q3_shared_favourites
MATCH (:User {userId:1})-[r1:RATED]->(m:Movie)<-[r2:RATED]-(:User {userId:2})
WHERE r1.rating >= 4 AND r2.rating >= 4
RETURN m.movieId AS movieId,m.title AS title,r1.rating AS user1Rating,r2.rating AS user2Rating
ORDER BY movieId;
// @name q4_genres
// "Стабільно високі": середнє >= 4, >= 1000 оцінок, >= 70% оцінок 4–5.
// Виводимо ВСІ жанри й прапорець, щоб не приховувати негативний результат.
MATCH (g:Genre)<-[:HAS_GENRE]-(m:Movie)<-[r:RATED]-(:User)
WITH g,count(r) AS ratingCount,count(DISTINCT m) AS ratedMovies,
     avg(r.rating) AS averageRating,stDevP(r.rating) AS ratingStdDev,
     avg(CASE WHEN r.rating >= 4 THEN 1.0 ELSE 0.0 END) AS highRatingShare
RETURN g.name AS genre,averageRating,ratingCount,ratedMovies,ratingStdDev,highRatingShare,
       averageRating >= 4 AND ratingCount >= 1000 AND highRatingShare >= 0.70 AS consistentlyHigh
ORDER BY averageRating DESC,genre;
// @name q5_recommendations
// Схожість = кількість спільних оцінок >=4; мінімум 3, top-50 сусідів.
MATCH (target:User {userId:1})-[a:RATED]->(:Movie)<-[b:RATED]-(other:User)
WHERE a.rating >= 4 AND b.rating >= 4 AND other <> target
WITH target,other,count(*) AS sharedLikes
WHERE sharedLikes >= 3
WITH target,other,sharedLikes
ORDER BY sharedLikes DESC,other.userId
LIMIT 50
MATCH (other)-[r:RATED]->(candidate:Movie)
WHERE r.rating >= 4 AND NOT EXISTS { MATCH (target)-[:RATED]->(candidate) }
WITH candidate,count(DISTINCT other) AS supporters,
     sum(sharedLikes) AS score,
     sum(toFloat(sharedLikes)*r.rating)/sum(sharedLikes) AS weightedRating
WHERE supporters >= 2
RETURN candidate.movieId AS movieId,candidate.title AS title,score,supporters,weightedRating
ORDER BY score DESC,supporters DESC,weightedRating DESC,movieId
LIMIT 10;
// @name q6_shortest_path
// Лише RATED, без жанрових скорочень. Напрям ігноруємо навмисно.
MATCH (a:User {userId:1}),(b:User {userId:2})
MATCH p=shortestPath((a)-[:RATED*]-(b))
RETURN length(p) AS hops,
       [n IN nodes(p) | CASE WHEN n:User THEN 'User '+toString(n.userId) ELSE n.title END] AS chain;
