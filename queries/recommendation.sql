-- Еквівалент Q5: стандартні CTE, JOIN, NOT EXISTS, GROUP BY.
WITH neighbours AS (
 SELECT b.userId, COUNT(*) AS sharedLikes
 FROM ratings a JOIN ratings b ON a.movieId=b.movieId
 WHERE a.userId=1 AND b.userId<>1 AND a.rating>=4 AND b.rating>=4
 GROUP BY b.userId
 HAVING COUNT(*)>=3
 ORDER BY sharedLikes DESC,b.userId
 LIMIT 50
)
SELECT m.movieId,m.title,SUM(n.sharedLikes) AS score,
       COUNT(DISTINCT n.userId) AS supporters,
       SUM(1.0*n.sharedLikes*r.rating)/SUM(n.sharedLikes) AS weightedRating
FROM neighbours n
JOIN ratings r ON r.userId=n.userId
JOIN movies m ON m.movieId=r.movieId
WHERE r.rating>=4
 AND NOT EXISTS (
   SELECT 1 FROM ratings seen WHERE seen.userId=1 AND seen.movieId=m.movieId
 )
GROUP BY m.movieId,m.title
HAVING COUNT(DISTINCT n.userId)>=2
ORDER BY score DESC,supporters DESC,weightedRating DESC,m.movieId
LIMIT 10;
