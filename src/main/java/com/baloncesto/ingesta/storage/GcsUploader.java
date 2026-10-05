package com.baloncesto.ingesta.storage;

import com.baloncesto.ingesta.config.AppConfig;

/**
 * Sube bytes crudos (JSON sin transformar) al bucket de GCS configurado,
 * usando el SDK oficial de Google Cloud y Application Default Credentials.
 */
public final class GcsUploader {

    /**
     * @param config configuracion de la aplicacion (provee bucket y projectId)
     */
    public GcsUploader(AppConfig config) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }

    /**
     * Sube el contenido indicado al bucket configurado, en el path dado.
     *
     * @param objectPath path relativo dentro del bucket (p.ej. generado por {@link BronzePathBuilder})
     * @param content    contenido crudo a subir (bytes del JSON tal como llego de la API)
     * @return la URI completa {@code gs://bucket/path} del objeto subido
     */
    public String upload(String objectPath, byte[] content) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
