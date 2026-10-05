package com.baloncesto.ingesta.http;

/**
 * Backoff exponencial con jitter, aplicado unicamente ante respuestas
 * 429 (rate limited), 403 (bloqueo/headers invalidos) o 5xx (error del servidor).
 *
 * <p>Formula prevista: {@code delay = min(baseDelay * 2^intento + jitter(0, baseDelay), maxDelay)}.
 */
public final class RetryPolicy {

    /**
     * @param maxRetries      numero maximo de reintentos antes de abandonar la tarea
     * @param baseDelayMillis delay base usado en la formula de backoff exponencial
     * @param maxDelayMillis  tope maximo de espera entre reintentos
     */
    public RetryPolicy(int maxRetries, long baseDelayMillis, long maxDelayMillis) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }

    /**
     * Decide si corresponde reintentar una peticion dado el intento actual
     * y el codigo de estado HTTP recibido.
     *
     * @param attempt        numero de intento ya realizado (1-indexado)
     * @param httpStatusCode codigo de estado HTTP de la respuesta recibida
     * @return {@code true} si se debe reintentar, {@code false} si se debe abandonar la tarea
     */
    public boolean shouldRetry(int attempt, int httpStatusCode) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }

    /**
     * Calcula el tiempo de espera antes del siguiente reintento, aplicando
     * backoff exponencial con jitter y respetando el tope maximo configurado.
     *
     * @param attempt numero de intento que esta por realizarse (1-indexado)
     * @return milisegundos a esperar antes de reintentar
     */
    public long computeDelayMillis(int attempt) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
