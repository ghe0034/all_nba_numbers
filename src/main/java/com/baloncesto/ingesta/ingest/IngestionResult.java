package com.baloncesto.ingesta.ingest;

/**
 * Resultado de ejecutar una {@code IngestionTask}: exito o fallo, mas
 * la metadata necesaria para el resumen final del batch y para los logs.
 *
 * @param endpointId    identificador de la variante de endpoint procesada
 * @param season        temporada procesada, en formato {@code "YYYY-YY"}
 * @param success        {@code true} si la descarga y subida a GCS fueron exitosas
 * @param gcsPath        URI {@code gs://...} del objeto subido, o {@code null} si fallo
 * @param errorMessage   mensaje de error, o {@code null} si {@code success} es {@code true}
 */
public record IngestionResult(
        String endpointId,
        String season,
        boolean success,
        String gcsPath,
        String errorMessage
) {
}
