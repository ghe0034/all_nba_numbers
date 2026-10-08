package com.baloncesto.ingesta.http;

import com.baloncesto.ingesta.config.AppConfig;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Centraliza los headers HTTP que stats.nba.com exige para no responder 403.
 *
 * <p>Este es el unico lugar del proyecto que debe tocarse si la NBA cambia
 * sus requisitos de headers (User-Agent, Referer, Origin, x-nba-stats-*, etc.).
 */
public final class NbaStatsHeaders {

    /** User-Agent usado cuando no se provee uno explicito. */
    public static final String DEFAULT_USER_AGENT =
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    + "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

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
        return buildHeaders(config == null ? null : config.httpUserAgent());
    }

    /**
     * Igual que {@link #buildHeaders(AppConfig)} pero con el User-Agent explicito.
     *
     * @param userAgentOverride User-Agent a usar; si es {@code null} o vacio se usa {@link #DEFAULT_USER_AGENT}
     * @return mapa de headers nombre -&gt; valor
     */
    public static Map<String, String> buildHeaders(String userAgentOverride) {
        String userAgent = (userAgentOverride == null || userAgentOverride.isBlank())
                ? DEFAULT_USER_AGENT
                : userAgentOverride;

        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("User-Agent", userAgent);
        headers.put("Accept", "application/json, text/plain, */*");
        headers.put("Accept-Language", "en-US,en;q=0.9");
        headers.put("Accept-Encoding", "gzip");
        headers.put("Connection", "keep-alive");
        headers.put("Host", "stats.nba.com");
        headers.put("Origin", "https://www.nba.com");
        headers.put("Referer", "https://www.nba.com/");
        headers.put("x-nba-stats-origin", "stats");
        headers.put("x-nba-stats-token", "true");
        headers.put("Sec-Fetch-Dest", "empty");
        headers.put("Sec-Fetch-Mode", "cors");
        headers.put("Sec-Fetch-Site", "same-site");
        return headers;
    }
}
