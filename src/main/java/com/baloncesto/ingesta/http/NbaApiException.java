package com.baloncesto.ingesta.http;

/**
 * Error irrecuperable al consultar un endpoint de stats.nba.com, lanzado
 * cuando {@code RetryPolicy} agota los reintentos permitidos.
 */
public final class NbaApiException extends RuntimeException {

    private final int httpStatusCode;
    private final String endpointId;

    /**
     * @param message        descripcion del error
     * @param httpStatusCode ultimo codigo de estado HTTP recibido (o -1 si no hubo respuesta)
     * @param endpointId     identificador de la variante de endpoint que fallo
     * @param cause          causa original (p.ej. excepcion de red), puede ser {@code null}
     */
    public NbaApiException(String message, int httpStatusCode, String endpointId, Throwable cause) {
        super(message, cause);
        this.httpStatusCode = httpStatusCode;
        this.endpointId = endpointId;
    }

    /**
     * @return el ultimo codigo de estado HTTP recibido, o -1 si no hubo respuesta
     */
    public int httpStatusCode() {
        return httpStatusCode;
    }

    /**
     * @return el identificador de la variante de endpoint que fallo
     */
    public String endpointId() {
        return endpointId;
    }
}
