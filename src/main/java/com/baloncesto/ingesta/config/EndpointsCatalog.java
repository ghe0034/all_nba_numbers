package com.baloncesto.ingesta.config;

import java.util.List;

/**
 * Carga el catalogo de endpoints desde {@code src/main/resources/endpoints.json}.
 *
 * <p>El catalogo externo permite agregar o modificar variantes de endpoint
 * (por ejemplo cambiar {@code SeasonType}, o agregar un nuevo endpoint)
 * sin recompilar la aplicacion.
 */
public final class EndpointsCatalog {

    /**
     * @param resourcePath ruta del recurso JSON dentro del classpath
     *                     (p.ej. {@code "/endpoints.json"})
     */
    public EndpointsCatalog(String resourcePath) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }

    /**
     * Lee y deserializa el catalogo completo de endpoints.
     *
     * @return lista de {@code EndpointDefinition} declaradas en el catalogo
     */
    public List<EndpointDefinition> loadAll() {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
