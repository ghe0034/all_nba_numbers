package com.baloncesto.ingesta.http;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class RetryPolicyTest {

    private static final long BASE = 100;
    private static final long MAX = 5_000;

    private final RetryPolicy policy = new RetryPolicy(3, BASE, MAX);

    @Test
    void delayGrowsWithEachAttempt() {
        // Rango por intento n: [BASE*2^n, BASE*2^n + BASE), disjunto del siguiente.
        long previous = -1;
        for (int attempt = 1; attempt <= 4; attempt++) {
            long delay = policy.computeDelayMillis(attempt);
            long lower = BASE * (1L << attempt);
            assertTrue(delay >= lower && delay < lower + BASE,
                    "Intento " + attempt + " fuera de rango: " + delay);
            assertTrue(delay > previous, "El delay debe crecer: " + delay + " <= " + previous);
            previous = delay;
        }
    }

    @Test
    void delayNeverExceedsMax() {
        for (int attempt = 1; attempt <= 100; attempt++) {
            assertTrue(policy.computeDelayMillis(attempt) <= MAX);
        }
        assertEquals(MAX, policy.computeDelayMillis(100));
    }

    @Test
    void retriesOnRateLimitForbiddenAndServerErrors() {
        assertTrue(policy.shouldRetry(1, 429));
        assertTrue(policy.shouldRetry(1, 403));
        assertTrue(policy.shouldRetry(1, 500));
        assertTrue(policy.shouldRetry(1, 503));
    }

    @Test
    void doesNotRetryOnSuccessOrOtherClientErrors() {
        assertFalse(policy.shouldRetry(1, 200));
        assertFalse(policy.shouldRetry(1, 404));
        assertFalse(policy.shouldRetry(1, 400));
    }

    @Test
    void stopsRetryingWhenAttemptsExhausted() {
        assertTrue(policy.shouldRetry(3, 429));
        assertFalse(policy.shouldRetry(4, 429));
    }

    @Test
    void rejectsInvalidConfiguration() {
        assertThrows(IllegalArgumentException.class, () -> new RetryPolicy(-1, BASE, MAX));
        assertThrows(IllegalArgumentException.class, () -> new RetryPolicy(3, 0, MAX));
        assertThrows(IllegalArgumentException.class, () -> new RetryPolicy(3, BASE, BASE - 1));
    }
}
