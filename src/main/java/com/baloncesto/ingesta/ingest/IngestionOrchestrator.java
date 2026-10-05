package com.baloncesto.ingesta.ingest;

import com.baloncesto.ingesta.config.AppConfig;
import com.baloncesto.ingesta.config.EndpointsCatalog;
import com.baloncesto.ingesta.http.NbaStatsHttpClient;
import com.baloncesto.ingesta.storage.GcsUploader;

import java.util.List;

/**
 * Orquesta el batch completo: recorre todas las combinaciones de
 * (variante de endpoint x temporada) definidas por {@code EndpointsCatalog}
 * y {@code SeasonRange}, ejecuta cada {@code IngestionTask} y produce
 * un resumen final de exitos y fallos.
 */
public final class IngestionOrchestrator {

    /**
     * @param config     configuracion de la aplicacion (cantidad de temporadas, anio final, etc.)
     * @param catalog    catalogo de variantes de endpoint a procesar
     * @param httpClient cliente HTTP configurado para stats.nba.com
     * @param uploader   cliente de subida a GCS
     */
    public IngestionOrchestrator(
            AppConfig config,
            EndpointsCatalog catalog,
            NbaStatsHttpClient httpClient,
            GcsUploader uploader
    ) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }

    /**
     * Ejecuta secuencialmente todas las tareas del batch, continuando ante
     * fallos parciales, y registra un resumen final (total/exitos/fallos) en el log.
     *
     * @return la lista de resultados de todas las tareas ejecutadas
     */
    public List<IngestionResult> runAll() {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
