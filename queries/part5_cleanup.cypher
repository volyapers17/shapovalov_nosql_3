// Виконувати ЛИШЕ після збереження результатів і візуалізацій.
// @name cleanup_movie_projection
CALL gds.graph.drop('movieGraph',false) YIELD graphName RETURN graphName;
// @name cleanup_user_projection
CALL gds.graph.drop('userGraph',false) YIELD graphName RETURN graphName;
// @name cleanup_derived
MATCH ()-[r:CO_RATED|SIMILAR]->() DELETE r;
// @name cleanup_communities
MATCH (u:User) REMOVE u.community;
