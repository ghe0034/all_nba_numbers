package com.baloncesto.ingesta.config;

import java.util.List;

/**
 * Calcula el rango de temporadas historicas a descargar, en el formato
 * esperado por stats.nba.com ({@code "YYYY-YY"}, p.ej. {@code "2023-24"}).
 */
public final class SeasonRange {

    private SeasonRange() {
        // Utilidad estatica, no instanciable.
    }

    /**
     * Genera las ultimas {@code count} temporadas terminando en {@code endYear}.
     *
     * @param count   cantidad de temporadas a generar (p.ej. 10)
     * @param endYear anio de inicio de la temporada mas reciente (p.ej. 2025 para "2025-26")
     * @return lista de temporadas en formato {@code "YYYY-YY"}, ordenadas de mas antigua a mas reciente
     */
    public static List<String> lastNSeasons(int count, int endYear) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
