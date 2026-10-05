package com.baloncesto.ingesta.config;

import java.util.Map;

/**
 * Define una variante de peticion contra un endpoint de stats.nba.com,
 * tal como se declara en {@code src/main/resources/endpoints.json}.
 *
 * <p>Ejemplo: la variante {@code leaguegamelog_player} usa el path
 * {@code leaguegamelog} con el parametro fijo {@code PlayerOrTeam=P},
 * y requiere que se le inyecte dinamicamente el parametro {@code Season}
 * para cada temporada a descargar.
 *
 * @param id              identificador unico de la variante (usado en el path de GCS)
 * @param path             path relativo del endpoint en stats.nba.com (sin host)
 * @param fixedParams      parametros de query fijos para esta variante (p.ej. PlayerOrTeam=P)
 * @param seasonParamName  nombre del parametro de query donde se inyecta la temporada (p.ej. "Season")
 */
public record EndpointDefinition(
        String id,
        String path,
        Map<String, String> fixedParams,
        String seasonParamName
) {
}
