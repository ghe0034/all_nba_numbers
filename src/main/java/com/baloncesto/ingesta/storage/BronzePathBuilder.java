package com.baloncesto.ingesta.storage;

import java.time.Instant;

/**
 * Construye el path particionado dentro del bucket de GCS para la capa Bronze.
 *
 * <p>Patron: {@code bronze/{endpointId}/season={season}/download_date={yyyy-MM-dd}/{endpointId}_{season}_{timestamp}.json}
 */
public final class BronzePathBuilder {

    private BronzePathBuilder() {
        // Utilidad estatica, no instanciable.
    }

    /**
     * Construye el path completo del objeto a subir a GCS (sin el nombre del bucket).
     *
     * @param endpointId         identificador de la variante de endpoint (p.ej. "leaguegamelog_player")
     * @param season             temporada en formato {@code "YYYY-YY"}
     * @param downloadTimestamp  instante en que se descargo el archivo, usado para
     *                           particionar por fecha y evitar sobreescrituras
     * @return path relativo dentro del bucket, listo para usar como nombre de objeto
     */
    public static String buildPath(String endpointId, String season, Instant downloadTimestamp) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
