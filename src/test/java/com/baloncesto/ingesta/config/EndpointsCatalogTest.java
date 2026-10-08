package com.baloncesto.ingesta.config;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;

class EndpointsCatalogTest {

    private final List<EndpointDefinition> all = new EndpointsCatalog("/endpoints.json").loadAll();
    private final Map<String, EndpointDefinition> byId =
            all.stream().collect(Collectors.toMap(EndpointDefinition::id, Function.identity()));

    @Test
    void loadsTheFourVariants() {
        assertEquals(4, all.size());
        assertEquals(
                Set.of("leaguegamelog_player", "leaguegamelog_team",
                        "leaguedashteamstats", "commonallplayers"),
                byId.keySet());
    }

    @Test
    void playerAndTeamGameLogsDifferInPlayerOrTeam() {
        EndpointDefinition player = byId.get("leaguegamelog_player");
        EndpointDefinition team = byId.get("leaguegamelog_team");
        assertEquals("/stats/leaguegamelog", player.path());
        assertEquals("/stats/leaguegamelog", team.path());
        assertEquals("P", player.fixedParams().get("PlayerOrTeam"));
        assertEquals("T", team.fixedParams().get("PlayerOrTeam"));
    }

    @Test
    void everyEndpointIsFullyDefined() {
        for (EndpointDefinition e : all) {
            assertTrue(e.path().startsWith("/stats/"), e.id());
            assertEquals("Season", e.seasonParamName(), e.id());
            assertTrue(e.fixedParams().containsKey("LeagueID"), e.id());
            assertFalse(e.fixedParams().containsKey("Season"),
                    "Season se inyecta dinamicamente: " + e.id());
        }
    }

    @Test
    void teamStatsAndAllPlayersHaveRequiredParams() {
        assertEquals("Base", byId.get("leaguedashteamstats").fixedParams().get("MeasureType"));
        assertEquals("PerGame", byId.get("leaguedashteamstats").fixedParams().get("PerMode"));
        assertEquals("0", byId.get("commonallplayers").fixedParams().get("IsOnlyCurrentSeason"));
    }

    @Test
    void missingResourceFails() {
        assertThrows(IllegalStateException.class, () -> new EndpointsCatalog("/no-existe.json").loadAll());
    }
}
