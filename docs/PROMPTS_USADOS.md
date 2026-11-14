Documento que almacena los prompts usados en Claude Code en este proyecto.
Este documento debe ser ignorado por completo por Claude.
1. Definición del Plan Inicial (Fase 1)
Rol y Objetivo: Actúa como un Data Engineer Senior. Planifica la estructura de carpetas y el plan de desarrollo paso a paso exclusivamente para la Fase 1 de un proyecto de datos de la NBA. No incluyas bases de datos relacionales, transformaciones, ni automatización semanal en esta fase.

Alcance de la Fase 1 (Ingesta Histórica y Capa Bronze):
Crear una aplicación batch en Java que descargue los datos de las últimas 10 temporadas desde los endpoints REST de stats.nba.com y los suba como archivos JSON en bruto (sin alterar) a un bucket de Google Cloud Storage.

Contexto Técnico y Restricciones:

Lenguaje: Java puro (usa el HttpClient nativo introducido en Java 11). Evita frameworks pesados como Spring Boot para este script.

Gestor de dependencias: Maven o Gradle (elije uno y configúralo).

Nube: Google Cloud Storage (usa el SDK oficial de Java para GCP).

Reto Técnico: Detalla en el plan cómo la aplicación debe gestionar los HTTP Headers (User-Agent, Referer, etc.) y los tiempos de espera (Rate Limiting) para evitar bloqueos por parte del servidor de la NBA.

Entregables que necesito de este plan:

La estructura de directorios y archivos propuesta.

Las dependencias exactas que debo añadir al pom.xml o build.gradle.

Un archivo PLAN_FASE1.md con las tareas de desarrollo secuenciales para construir y probar este flujo histórico de ingesta a GCP.

2. Corrección de la Estrategia de Extracción (Evitar Baneos)
No quiero ninguna de esas tres opciones porque playergamelog es ineficiente para una carga histórica masiva. Rechazo el uso de ese endpoint.

En su lugar, incluye en la Fase 1 el uso del endpoint leaguegamelog. Este endpoint nos permite obtener el registro de partidos de todos los jugadores de una temporada completa en una sola petición (usando el parámetro PlayerOrTeam=Player y pasando el Season).

De esta forma, descargaremos el 100% de los datos históricos haciendo solo 1 petición por temporada (10 peticiones en total) con un pequeño Thread.sleep() entre ellas, evitando por completo el riesgo de baneo y sin perder datos.

3. Ejecución del Esqueleto del Proyecto (Contratos e Interfaces)
El plan es brillante. Has captado perfectamente los requisitos de resiliencia y la estructura de partición en GCS.

Vamos a empezar la ejecución de la Fase 1 creando únicamente el esqueleto. Por favor, ejecuta las siguientes tareas y luego detente por completo:

Crea la estructura de directorios exacta dentro de proyecto_baloncesto/.

Crea los archivos base: .gitignore, el pom.xml con las dependencias exactas que listaste, y los archivos .properties en la carpeta config.

Crea todas las clases mencionadas (App, NbaStatsHttpClient, GcsUploader, IngestionOrchestrator, RateLimiter, RetryPolicy, etc.).
REGLA ESTRICTA: No implementes la lógica interna de ningún método. Escribe únicamente las firmas de los métodos públicos, añade un comentario JavaDoc explicando sus responsabilidades y parámetros, y haz que el cuerpo del método retorne null o lance new UnsupportedOperationException("Not implemented yet");.

Crea el archivo ARCHITECTURE.md incluyendo un diagrama Mermaid (flowchart TD) que visualice el flujo de una IngestionTask: desde el Orquestador, pasando por el RateLimiter y el Cliente HTTP (mostrando el bucle de Retry), hasta la subida a GCS mediante el Uploader.

Confírmame cuando hayas creado estos archivos. Revisaré los contratos (firmas) de las clases antes de darte luz verde para implementar la lógica de red o de almacenamiento.

4. Definición de Reglas del Sistema (CLAUDE.md) y Catálogo
Antes de pasar al cliente HTTP, vamos a fijar las reglas del proyecto para que no tengas que trabajar de memoria.

Crea un archivo llamado CLAUDE.md en la raíz del proyecto. Este archivo actuará como tus instrucciones de sistema para este repositorio. Debe incluir:

Rol: Actuar como Data Engineer Senior.

Stack: Java 17 puro, Maven, nativo HttpClient. Prohibido usar Spring Boot o frameworks pesados.

Regla de Ejecución: Nunca implementar lógica sin definir primero el contrato (esqueleto) y escribir los tests unitarios.

Regla de APIs: NUNCA inventar o asumir parámetros de red de memoria. Si un endpoint (como leaguedashteamstats) requiere parámetros exactos que desconoces, debes detenerte y pedirme que te los proporcione.

Respecto a tu comentario sobre leaguedashteamstats: bórralo de endpoints.json por ahora. Solo dejaremos leaguegamelog (para jugadores y equipos) para la prueba inicial, ya que esos parámetros sí los conocemos bien.

Confírmame cuando el CLAUDE.md esté creado y el JSON corregido.

5. Implementación del Cliente HTTP y Prueba de Integración
He probado las cabeceras manualmente en mi terminal y el servidor de la NBA me ha devuelto un 200 OK. Las defensas están superadas.

Vamos a dar el siguiente paso. Por favor, ejecuta únicamente lo siguiente y luego detente:

Implementa NbaStatsHttpClient.java: Usa el HttpClient nativo de Java 17. Este cliente debe usar la clase NbaStatsHeaders que creaste antes para inyectar todas las cabeceras en cada petición.

Integra la resiliencia: Antes de llamar a HttpClient.send(), el método debe invocar a RateLimiter.acquire() para aplicar el throttle proactivo. Si la petición devuelve un 429, 403 o 5xx, debe delegar en RetryPolicy para gestionar el backoff exponencial. Si la respuesta contiene Content-Encoding: gzip, debe descomprimir el body automáticamente.

Prueba de Integración Real: Crea un test de integración (ej. NbaStatsHttpClientIT.java o un método main temporal) que intente hacer una única llamada real al endpoint leaguegamelog (Player) para la temporada 2023-24. Debe imprimir por consola el status code y los primeros 200 caracteres del JSON resultante.

REGLA ESTRICTA: No implementes todavía nada relacionado con el Orquestador o Google Cloud Storage. Confírmame cuando tengas el cliente listo para que yo pueda ejecutar esa prueba de integración en mi ordenador.