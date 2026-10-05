package com.baloncesto.ingesta.http;

import com.baloncesto.ingesta.config.AppConfig;

import java.util.Map;

/**
 * Centraliza los headers HTTP que stats.nba.com exige para no responder 403.
 *
 * <p>Este es el unico lugar del proyecto que debe tocarse si la NBA cambia
 * sus requisitos de headers (User-Agent, Referer, Origin, x-nba-stats-*, etc.).
 */
public final class NbaStatsHeaders {

    private NbaStatsHeaders() {
        // Utilidad estatica, no instanciable.
    }

    /**
     * Construye el mapa completo de headers a enviar en cada request a
     * stats.nba.com, incluyendo el User-Agent configurable via {@code AppConfig}.
     *
     * @param config configuracion de la aplicacion (provee el User-Agent override-able)
     * @return mapa de headers nombre -&gt; valor
     */
    public static Map<String, String> buildHeaders(AppConfig config) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
