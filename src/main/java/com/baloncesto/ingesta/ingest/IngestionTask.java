package com.baloncesto.ingesta.ingest;

import com.baloncesto.ingesta.config.EndpointDefinition;
import com.baloncesto.ingesta.http.NbaStatsHttpClient;
import com.baloncesto.ingesta.storage.GcsUploader;

/**
 * Unidad de trabajo del batch: descarga una (endpoint, temporada) y sube
 * el resultado crudo a GCS. Un fallo en una tarea no debe interrumpir
 * la ejecucion de las demas tareas del batch.
 */
public final class IngestionTask {

    /**
     * @param endpoint variante de endpoint a descargar
     * @param season   temporada a descargar, en formato {@code "YYYY-YY"}
     */
    public IngestionTask(EndpointDefinition endpoint, String season) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }

    /**
     * Ejecuta la descarga via {@code httpClient} y la subida via {@code uploader},
     * capturando cualquier error y convirtiendolo en un {@link IngestionResult} fallido
     * en vez de propagar la excepcion.
     *
     * @param httpClient cliente HTTP configurado para stats.nba.com
     * @param uploader   cliente de subida a GCS
     * @return el resultado de la tarea, exitoso o fallido
     */
    public IngestionResult execute(NbaStatsHttpClient httpClient, GcsUploader uploader) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
