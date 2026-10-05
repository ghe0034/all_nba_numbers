package com.baloncesto.ingesta.util;

/**
 * Utilidades minimas sobre JSON crudo. No realiza ninguna transformacion:
 * solo valida que el contenido descargado sea JSON parseable antes de subirlo.
 */
public final class JsonUtils {

    private JsonUtils() {
        // Utilidad estatica, no instanciable.
    }

    /**
     * Verifica que el contenido indicado sea JSON sintacticamente valido.
     *
     * @param content contenido crudo recibido de stats.nba.com
     * @return {@code true} si el contenido es JSON parseable, {@code false} en caso contrario
     */
    public static boolean isValidJson(String content) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
