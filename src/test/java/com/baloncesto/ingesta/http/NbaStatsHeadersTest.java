package com.baloncesto.ingesta.http;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.baloncesto.ingesta.config.AppConfig;
import java.util.Map;
import org.junit.jupiter.api.Test;

class NbaStatsHeadersTest {

    @Test
    void includesAllRequiredHeaders() {
        Map<String, String> h = NbaStatsHeaders.buildHeaders((String) null);

        assertEquals("https://www.nba.com", h.get("Origin"));
        assertEquals("https://www.nba.com/", h.get("Referer"));
        assertEquals("stats", h.get("x-nba-stats-origin"));
        assertEquals("true", h.get("x-nba-stats-token"));
        assertEquals("stats.nba.com", h.get("Host"));
        assertTrue(h.get("Accept").contains("application/json"));
        assertEquals("gzip", h.get("Accept-Encoding"));
        assertTrue(h.containsKey("Accept-Language"));
        assertEquals(NbaStatsHeaders.DEFAULT_USER_AGENT, h.get("User-Agent"));
    }

    @Test
    void userAgentIsOverridden() {
        Map<String, String> h = NbaStatsHeaders.buildHeaders("MiAgente/1.0");
        assertEquals("MiAgente/1.0", h.get("User-Agent"));
        assertEquals("https://www.nba.com/", h.get("Referer"));
    }

    @Test
    void blankUserAgentFallsBackToDefault() {
        assertEquals(NbaStatsHeaders.DEFAULT_USER_AGENT,
                NbaStatsHeaders.buildHeaders("  ").get("User-Agent"));
    }

    @Test
    void userAgentComesFromAppConfig() {
        AppConfig config = new AppConfig("b", "p", 1, 1, 1, 1, "ConfigUA/2.0", 1, 1, 10, 2025);
        assertEquals("ConfigUA/2.0", NbaStatsHeaders.buildHeaders(config).get("User-Agent"));
    }
}
