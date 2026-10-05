package com.baloncesto.ingesta.http;

/**
 * Throttle proactivo entre peticiones consecutivas a stats.nba.com.
 *
 * <p>Se aplica siempre, antes de cada request (exitoso o no), para evitar
 * generar el patron de rafaga que provoca bloqueos (429), en vez de solo
 * reaccionar despues de que ya ocurrieron.
 */
public final class RateLimiter {

    /**
     * @param minDelayMillis delay minimo garantizado entre el inicio de dos
     *                       peticiones consecutivas
     */
    public RateLimiter(long minDelayMillis) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }

    /**
     * Bloquea el hilo actual el tiempo necesario para respetar el delay
     * minimo configurado desde la ultima invocacion a este metodo.
     */
    public void acquire() {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
