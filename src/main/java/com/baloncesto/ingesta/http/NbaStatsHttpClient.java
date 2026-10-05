package com.baloncesto.ingesta.http;

import com.baloncesto.ingesta.config.AppConfig;
import com.baloncesto.ingesta.config.EndpointDefinition;

import java.util.Map;

/**
 * Unico punto de la aplicacion que envia peticiones HTTP a stats.nba.com.
 *
 * <p>Flujo previsto por cada llamada a {@link #get(EndpointDefinition, Map)}:
 * <ol>
 *   <li>Construir la URL con los query params (fijos de la variante + dinamicos).</li>
 *   <li>Aplicar los headers de {@link NbaStatsHeaders}.</li>
 *   <li>Esperar el turno asignado por el {@link RateLimiter} antes de enviar.</li>
 *   <li>Enviar la peticion con {@code java.net.http.HttpClient}.</li>
 *   <li>Si la respuesta es 429/403/5xx, delegar en {@link RetryPolicy} para decidir
 *       si reintentar y cuanto esperar.</li>
 *   <li>Si la respuesta trae {@code Content-Encoding: gzip}, descomprimirla.</li>
 *   <li>Devolver el body crudo, o lanzar {@link NbaApiException} si se agotan los reintentos.</li>
 * </ol>
 */
public final class NbaStatsHttpClient {

    /**
     * @param config      configuracion de la aplicacion (timeouts, User-Agent, host, etc.)
     * @param rateLimiter throttle a aplicar antes de cada request
     * @param retryPolicy politica de backoff ante errores recuperables
     */
    public NbaStatsHttpClient(AppConfig config, RateLimiter rateLimiter, RetryPolicy retryPolicy) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }

    /**
     * Ejecuta una peticion GET contra la variante de endpoint indicada,
     * aplicando headers, rate limiting y reintentos segun corresponda.
     *
     * @param endpoint variante de endpoint a consultar
     * @param params   parametros de query dinamicos (p.ej. {@code Season=2023-24})
     * @return el body de la respuesta, en crudo, sin parsear
     * @throws NbaApiException si se agotan los reintentos sin obtener una respuesta valida
     */
    public String get(EndpointDefinition endpoint, Map<String, String> params) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
