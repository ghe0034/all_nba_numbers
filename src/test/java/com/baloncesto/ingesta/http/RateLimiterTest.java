package com.baloncesto.ingesta.http;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class RateLimiterTest {

    private static final long MIN_DELAY_MS = 200;

    @Test
    void secondConsecutiveCallBlocksForMinimumDelay() {
        RateLimiter limiter = new RateLimiter(MIN_DELAY_MS);

        long start = System.nanoTime();
        limiter.acquire();
        limiter.acquire();
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;

        assertTrue(elapsedMs >= MIN_DELAY_MS,
                "Esperaba >= " + MIN_DELAY_MS + " ms pero fueron " + elapsedMs);
    }

    @Test
    void firstCallDoesNotBlock() {
        RateLimiter limiter = new RateLimiter(MIN_DELAY_MS);

        long start = System.nanoTime();
        limiter.acquire();
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;

        assertTrue(elapsedMs < MIN_DELAY_MS, "La primera llamada no debe bloquear: " + elapsedMs);
    }

    @Test
    void doesNotWaitAgainIfDelayAlreadyElapsed() throws InterruptedException {
        RateLimiter limiter = new RateLimiter(50);
        limiter.acquire();
        Thread.sleep(100);

        long start = System.nanoTime();
        limiter.acquire();
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;

        assertTrue(elapsedMs < 40, "No debia esperar de nuevo: " + elapsedMs);
    }

    @Test
    void rejectsNegativeDelay() {
        assertThrows(IllegalArgumentException.class, () -> new RateLimiter(-1));
    }
}
