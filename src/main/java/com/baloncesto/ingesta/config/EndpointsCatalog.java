package com.baloncesto.ingesta.config;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.util.List;

/**
 * Carga el catalogo de endpoints desde {@code src/main/resources/endpoints.json}.
 *
 * <p>El catalogo externo permite agregar o modificar variantes de endpoint
 * (por ejemplo cambiar {@code SeasonType}, o agregar un nuevo endpoint)
 * sin recompilar la aplicacion.
 */
public final class EndpointsCatalog {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final String resourcePath;

    /**
     * @param resourcePath ruta del recurso JSON dentro del classpath
     *                     (p.ej. {@code "/endpoints.json"})
     */
    public EndpointsCatalog(String resourcePath) {
        if (resourcePath == null || resourcePath.isBlank()) {
            throw new IllegalArgumentException("resourcePath es obligatorio");
        }
        this.resourcePath = resourcePath;
    }

    /**
     * Lee y deserializa el catalogo completo de endpoints.
     *
     * @return lista de {@code EndpointDefinition} declaradas en el catalogo
     */
    public List<EndpointDefinition> loadAll() {
        try (InputStream in = EndpointsCatalog.class.getResourceAsStream(resourcePath)) {
            if (in == null) {
                throw new IllegalStateException("Recurso no encontrado en el classpath: " + resourcePath);
            }
            return List.copyOf(MAPPER.readValue(in, new TypeReference<List<EndpointDefinition>>() { }));
        } catch (IOException e) {
            throw new UncheckedIOException("No se pudo leer el catalogo " + resourcePath, e);
        }
    }
}
