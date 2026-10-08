package com.baloncesto.ingesta.http;

/**
 * Throttle proactivo entre peticiones consecutivas a stats.nba.com.
 *
 * <p>Se aplica siempre, antes de cada request (exitoso o no), para evitar
 * generar el patron de rafaga que provoca bloqueos (429), en vez de solo
 * reaccionar despues de que ya ocurrieron.
 */
public final class RateLimiter {

    private final long minDelayNanos;
    private long nextAllowedNanos;
    private boolean firstCall = true;

    /**
     * @param minDelayMillis delay minimo garantizado entre el inicio de dos
     *                       peticiones consecutivas
     */
    public RateLimiter(long minDelayMillis) {
        if (minDelayMillis < 0) {
            throw new IllegalArgumentException("minDelayMillis no puede ser negativo");
        }
        this.minDelayNanos = minDelayMillis * 1_000_000L;
    }

    /**
     * Bloquea el hilo actual el tiempo necesario para respetar el delay
     * minimo configurado desde la ultima invocacion a este metodo.
     */
    public synchronized void acquire() {
        long now = System.nanoTime();
        if (!firstCall) {
            long remaining = nextAllowedNanos - now;
            if (remaining > 0) {
                try {
                    Thread.sleep(remaining / 1_000_000L, (int) (remaining % 1_000_000L));
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    throw new IllegalStateException("Interrumpido esperando el rate limiter", e);
                }
                now = System.nanoTime();
            }
        }
        firstCall = false;
        nextAllowedNanos = now + minDelayNanos;
    }
}
