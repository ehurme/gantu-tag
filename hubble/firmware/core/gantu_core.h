/*
 * gantu_core: on-tag summaries and the 13-byte Hubble payload for the 3 V sensor tag.
 *
 * Portable C99, no RTOS or vendor calls: the platform layer (TI SimpleLink F3 SDK + Hubble Device SDK on the
 * CC2340R5) feeds it accelerometer samples, a minute tick and environment samples, and hands the packed payload to
 * hubble_ble_advertise_get(). The same file builds on a PC for the unit tests in ../test/.
 *
 * Payload format: see ../../docs/payload_v1.md. Licence: MIT (see LICENSE-CODE).
 */
#ifndef GANTU_CORE_H
#define GANTU_CORE_H

#include <stdint.h>

#define GANTU_PAYLOAD_LEN 13
#define GANTU_PAYLOAD_VERSION 1

/* Defaults; all can be changed in gantu_config before gantu_init(). */
#define GANTU_DEFAULT_ODR_HZ 50           /* accelerometer output data rate */
#define GANTU_DEFAULT_STATIC_TAU_S 2      /* running-mean window for the static (gravity) component */
#define GANTU_DEFAULT_ACTIVE_MG 30        /* a minute is "active" if its mean VeDBA exceeds this (mg) */
#define GANTU_DEFAULT_ALIVE_WINDOW_H 24   /* alive = at least one active minute in this many hours */

typedef struct {
    uint16_t odr_hz;
    uint16_t static_tau_s;
    uint16_t active_mg;
    uint16_t alive_window_h;
} gantu_config;

typedef struct {
    gantu_config cfg;

    /* accelerometer / VeDBA */
    int32_t ema[3];              /* static component per axis, mg * 256 */
    uint8_t ema_primed;
    uint32_t ema_shift;          /* EMA weight = 2^-ema_shift */
    uint64_t vedba_mg_samples;   /* running sum of VeDBA in mg over all samples since gantu_init */
    uint64_t minute_mg_samples;  /* same, for the current minute */
    uint32_t minute_samples;

    /* activity */
    uint32_t minutes_since_active;  /* UINT32_MAX until the first active minute */
    uint32_t minute_in_hour;

    /* hourly bins for the rolling 24 h minima; bin 0 is the current (partial) hour */
    int32_t p_min_pa[24];        /* INT32_MAX = no sample in that hour */
    int16_t t_min_cc[24];        /* centi-degC, INT16_MAX = no sample */

    /* latest environment sample */
    int32_t p_pa;                /* -1 = none yet */
    int16_t t_cc;
    uint16_t light_raw;          /* 0..4095 ADC counts */
    uint16_t batt_mv;

    uint8_t msg_counter;
} gantu_state;

void gantu_default_config(gantu_config *cfg);
void gantu_init(gantu_state *s, const gantu_config *cfg);

/* One accelerometer sample in mg (call at odr_hz; a FIFO drain calls it once per sample). */
void gantu_accel_push(gantu_state *s, int16_t x_mg, int16_t y_mg, int16_t z_mg);

/* Call once per minute from the RTC. Closes the activity minute and rolls the hourly bins. */
void gantu_minute_tick(gantu_state *s);

/* Environment sample (e.g. every 5 min): pressure in Pa, temperature in centi-degC, light ADC 0..4095, battery mV. */
void gantu_env_sample(gantu_state *s, int32_t pressure_pa, int16_t temp_cc, uint16_t light_raw, uint16_t batt_mv);

/* Pack the current state into out[13] and advance the message counter. */
void gantu_pack_payload(gantu_state *s, uint8_t out[GANTU_PAYLOAD_LEN]);

/* Exposed for tests and for the decoders' reference values. */
uint32_t gantu_vedba_cum_units(const gantu_state *s);   /* 0.1 g*s, not yet wrapped to 24 bits */
uint8_t gantu_light_code(uint16_t light_raw);           /* 0..63: top 6 bits of the 12-bit ADC reading */

#endif
