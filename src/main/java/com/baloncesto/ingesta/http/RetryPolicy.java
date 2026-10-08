package com.baloncesto.ingesta.http;

import java.util.concurrent.ThreadLocalRandom;

/**
 * Backoff exponencial con jitter, aplicado unicamente ante respuestas
 * 429 (rate limited), 403 (bloqueo/headers invalidos) o 5xx (error del servidor).
 *
 * <p>Formula prevista: {@code delay = min(baseDelay * 2^intento + jitter(0, baseDelay), maxDelay)}.
 */
public final class RetryPolicy {

    private final int maxRetries;
    private final long baseDelayMillis;
    private final long maxDelayMillis;

    /**
     * @param maxRetries      numero maximo de reintentos antes de abandonar la tarea
     * @param baseDelayMillis delay base usado en la formula de backoff exponencial
     * @param maxDelayMillis  tope maximo de espera entre reintentos
     */
    public RetryPolicy(int maxRetries, long baseDelayMillis, long maxDelayMillis) {
        if (maxRetries < 0) {
            throw new IllegalArgumentException("maxRetries no puede ser negativo");
        }
        if (baseDelayMillis <= 0) {
            throw new IllegalArgumentException("baseDelayMillis debe ser > 0");
        }
        if (maxDelayMillis < baseDelayMillis) {
            throw new IllegalArgumentException("maxDelayMillis debe ser >= baseDelayMillis");
        }
        this.maxRetries = maxRetries;
        this.baseDelayMillis = baseDelayMillis;
        this.maxDelayMillis = maxDelayMillis;
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
        boolean retryable = httpStatusCode == 429 || httpStatusCode == 403
                || (httpStatusCode >= 500 && httpStatusCode <= 599);
        return retryable && attempt <= maxRetries;
    }

    /**
     * Calcula el tiempo de espera antes del siguiente reintento, aplicando
     * backoff exponencial con jitter y respetando el tope maximo configurado.
     *
     * @param attempt numero de intento que esta por realizarse (1-indexado)
     * @return milisegundos a esperar antes de reintentar
     */
    public long computeDelayMillis(int attempt) {
        // Con 2^40 ya se supera cualquier tope razonable; evita overflow en el shift.
        long exponential = baseDelayMillis * (1L << Math.min(Math.max(attempt, 0), 40));
        if (exponential <= 0 || exponential >= maxDelayMillis) {
            return maxDelayMillis;
        }
        long jitter = ThreadLocalRandom.current().nextLong(baseDelayMillis);
        return Math.min(exponential + jitter, maxDelayMillis);
    }
}
