package com.baloncesto.ingesta.config;

/**
 * Configuracion inmutable de la aplicacion, resultado de combinar
 * {@code config/application.properties} con overrides opcionales por
 * variables de entorno (prefijo {@code NBA_INGESTA_}).
 *
 * @param gcsBucketName               bucket de GCS donde se escribe la capa Bronze
 * @param gcsProjectId                proyecto de GCP asociado al bucket
 * @param rateLimiterMinDelayMillis   delay minimo entre peticiones consecutivas a stats.nba.com
 * @param retryMaxRetries             numero maximo de reintentos ante 429/403/5xx
 * @param retryBaseDelayMillis        delay base para el backoff exponencial
 * @param retryMaxDelayMillis         delay maximo permitido entre reintentos
 * @param httpUserAgent               User-Agent a enviar en cada request
 * @param httpConnectTimeoutMillis    timeout de conexion del HttpClient
 * @param httpRequestTimeoutMillis    timeout de respuesta por request
 * @param seasonsCount                cantidad de temporadas historicas a descargar
 * @param seasonsEndYear              anio final (mas reciente) del rango de temporadas
 */
public record AppConfig(
        String gcsBucketName,
        String gcsProjectId,
        long rateLimiterMinDelayMillis,
        int retryMaxRetries,
        long retryBaseDelayMillis,
        long retryMaxDelayMillis,
        String httpUserAgent,
        long httpConnectTimeoutMillis,
        long httpRequestTimeoutMillis,
        int seasonsCount,
        int seasonsEndYear
) {

    /**
     * Carga la configuracion desde {@code config/application.properties},
     * aplicando overrides desde {@code config/application.local.properties}
     * (si existe) y desde variables de entorno con prefijo {@code NBA_INGESTA_}.
     *
     * @return instancia de {@code AppConfig} lista para usar
     */
    public static AppConfig load() {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
