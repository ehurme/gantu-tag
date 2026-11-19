/*
 * Host test for gantu_core (build: make -C hubble/firmware/test).
 * Simulates three days on a bat: day roosts with a torpor dip, two hours of flight each night with a climb.
 * Prints one CSV line per payload (hex + the values gantu_core packed) for the Python/R decoder cross-checks,
 * and checks the physics: VeDBA of the flight bouts, alive/dead, 24 h minima.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "../core/gantu_core.h"

#define ODR 50
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)

static double noise(void) { return ((double)rand() / RAND_MAX - 0.5) * 2.0; } /* uniform -1..1 */

static void hexline(FILE *f, const uint8_t *p, const gantu_state *s, int alive, uint32_t vedba)
{
    for (int i = 0; i < GANTU_PAYLOAD_LEN; i++) fprintf(f, "%02x", p[i]);
    fprintf(f, ",%d,%u,%d,%d,%u\n", alive, vedba & 0xFFFFFF, (int)s->t_cc, (int)s->p_pa, (unsigned)s->batt_mv);
}

int main(int argc, char **argv)
{
    FILE *csv = argc > 1 ? fopen(argv[1], "w") : stdout;
    fprintf(csv, "hex,alive,vedba_units,t_cc,p_pa,batt_mv\n");
    srand(1);

    gantu_config cfg;
    gantu_default_config(&cfg);
    cfg.odr_hz = ODR;
    gantu_state s;
    gantu_init(&s, &cfg);

    uint8_t pay[GANTU_PAYLOAD_LEN];
    const double two_pi = 6.283185307179586;
    double flight_g_s = 0;  /* analytic VeDBA of the flight bouts, g*s */
    int minutes = 3 * 24 * 60 + 30 * 60; /* 3 days, then 30 h motionless (dead tag) */
    int dead_from = 3 * 24 * 60;

    for (int m = 0; m < minutes; m++) {
        int hour = (m / 60) % 24;
        int flying = (m < dead_from) && (hour == 21 || hour == 22);
        /* accelerometer: gravity on z, 1 mg noise; flight = 10 Hz wingbeat 0.8 g on z plus 0.3 g on x */
        for (int k = 0; k < 60 * ODR; k++) {
            double t = (m * 60.0) + (double)k / ODR;
            double x = noise(), y = noise(), z = 1000 + noise();
            if (flying) {
                double ph = two_pi * 10.0 * t;
                x += 300 * sin(ph + 1.0);
                z += 800 * sin(ph);
            }
            gantu_accel_push(&s, (int16_t)lround(x), (int16_t)lround(y), (int16_t)lround(z));
        }
        gantu_minute_tick(&s);

        if (m % 5 == 4) {
            /* pressure 1000 hPa, climbs 2000 Pa (~170 m) during flight; temperature 30 degC, torpor 8 degC 06-12 h */
            int32_t p = 100000 - (flying ? 2000 : 0) + (int32_t)(30 * sin(m / 300.0));
            int16_t tc = (hour >= 6 && hour < 12) ? 800 : 3000;
            uint16_t light = (hour >= 6 && hour < 18) ? 200 : 3500; /* dark in roost by day, LED Voc outside at night */
            uint16_t batt = (uint16_t)(3050 - m / 20);
            gantu_env_sample(&s, p, tc, light, batt);
        }
        if (m % 15 == 14) {
            uint32_t msa = s.minutes_since_active;
            int alive = msa != UINT32_MAX && msa < 24u * 60u;
            uint32_t v = gantu_vedba_cum_units(&s);
            gantu_pack_payload(&s, pay);
            hexline(csv, pay, &s, alive, v);
        }
        if (m == 22 * 60 + 5) { /* just after night 1's flight */
            CHECK(s.minutes_since_active < 10, "should be active after flight, msa=%u", s.minutes_since_active);
        }
    }

    /* Analytic flight VeDBA: |d| = |(300 sin(p+1), 0, 800 sin p)| sampled 5x per cycle, over 3 x 2 h */
    double acc = 0;
    for (int k = 0; k < 5; k++) {
        double p = two_pi * k / 5.0;
        double dx = 300 * sin(p + 1.0), dz = 800 * sin(p);
        acc += sqrt(dx * dx + dz * dz);
    }
    flight_g_s = (acc / 5.0) / 1000.0 * 3 * 2 * 3600;
    double got = gantu_vedba_cum_units(&s) / 10.0;
    double rest_s = (double)minutes * 60 - 3 * 2 * 3600;
    double noise_g_s = got - flight_g_s;
    fprintf(stderr, "VeDBA total %.1f g*s, flight analytic %.1f g*s, rest/noise %.1f g*s (%.2f mg mean at rest)\n",
            got, flight_g_s, noise_g_s, noise_g_s / rest_s * 1000);
    CHECK(fabs(noise_g_s / rest_s * 1000) < 3.0, "rest VeDBA should be ~noise level");
    CHECK(fabs(got - flight_g_s) / flight_g_s < 0.12, "flight VeDBA within 12%% of analytic");

    /* After 30 h without motion the tag must report dead */
    uint32_t msa = s.minutes_since_active;
    CHECK(msa >= 24u * 60u, "should be dead after 30 h motionless, msa=%u", msa);

    /* 24 h minimum pressure: the last flight (98000 Pa +/- 30) is > 24 h old by now, so min is the roost pressure */
    int32_t pmin = INT32_MAX;
    for (int i = 0; i < 24; i++) if (s.p_min_pa[i] < pmin) pmin = s.p_min_pa[i];
    CHECK(pmin > 99900, "24 h min pressure should have forgotten the old flight, got %d", pmin);

    if (csv != stdout) fclose(csv);
    fprintf(stderr, fails ? "%d FAILED\n" : "all C checks passed\n", fails);
    return fails != 0;
}
