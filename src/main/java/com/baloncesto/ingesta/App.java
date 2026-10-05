package com.baloncesto.ingesta;

/**
 * Punto de entrada de la aplicacion batch de ingesta historica.
 *
 * <p>Responsabilidades de alto nivel (a implementar):
 * <ul>
 *   <li>Cargar la configuracion de la aplicacion ({@code AppConfig}).</li>
 *   <li>Cargar el catalogo de endpoints ({@code EndpointsCatalog}).</li>
 *   <li>Construir el cliente HTTP y el uploader de GCS.</li>
 *   <li>Ejecutar el {@code IngestionOrchestrator} y reportar el resumen final.</li>
 *   <li>Terminar el proceso con exit code 0 si todas las tareas fueron exitosas,
 *       o 1 si hubo al menos un fallo.</li>
 * </ul>
 */
public final class App {

    private App() {
        // Clase de entrada, no instanciable.
    }

    /**
     * Arranca el batch de ingesta historica completo.
     *
     * @param args argumentos de linea de comandos (sin uso previsto en Fase 1)
     */
    public static void main(String[] args) {
        throw new UnsupportedOperationException("Pendiente de implementar");
    }
}
