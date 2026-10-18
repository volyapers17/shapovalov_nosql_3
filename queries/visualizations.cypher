// Запускати окремо у Neo4j Browser після part5_gds.cypher.
// Невеликі околи, а не повні проєкції та не кольорове розбиття Louvain.
// Browser може домальовувати інші наявні зв'язки між поверненими вузлами.
// @name movie_neighbourhood
MATCH p=(m:Movie {movieId:2858})-[r:CO_RATED]-(n:Movie)
RETURN p ORDER BY r.weight DESC LIMIT 12;
// @name user_neighbourhood
MATCH p=(u:User {userId:4169})-[r:SIMILAR]-(v:User)
RETURN p ORDER BY r.weight DESC LIMIT 15;
