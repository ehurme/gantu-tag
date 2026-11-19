/* gantu_core: see gantu_core.h and ../../docs/payload_v1.md. MIT licence. */
#include "gantu_core.h"

#include <string.h>

#define NO_P INT32_MAX
#define NO_T INT16_MAX

void gantu_default_config(gantu_config *cfg)
{
    cfg->odr_hz = GANTU_DEFAULT_ODR_HZ;
    cfg->static_tau_s = GANTU_DEFAULT_STATIC_TAU_S;
    cfg->active_mg = GANTU_DEFAULT_ACTIVE_MG;
    cfg->alive_window_h = GANTU_DEFAULT_ALIVE_WINDOW_H;
}

static uint32_t isqrt32(uint32_t v)
{
    uint32_t r = 0, bit = 1UL << 30;
    while (bit > v) bit >>= 2;
    while (bit) {
        if (v >= r + bit) {
            v -= r + bit;
            r = (r >> 1) + bit;
        } else {
            r >>= 1;
        }
        bit >>= 2;
    }
    return r;
}

void gantu_init(gantu_state *s, const gantu_config *cfg)
{
    memset(s, 0, sizeof(*s));
    if (cfg) s->cfg = *cfg; else gantu_default_config(&s->cfg);
    if (s->cfg.odr_hz == 0) s->cfg.odr_hz = GANTU_DEFAULT_ODR_HZ;

    /* EMA weight 2^-k with 2^k closest to tau * odr samples */
    uint32_t n = (uint32_t)s->cfg.static_tau_s * s->cfg.odr_hz, k = 0;
    while (k < 15 && (1UL << (k + 1)) <= n + (n >> 1)) k++;
    s->ema_shift = k;

    s->minutes_since_active = UINT32_MAX;
    for (int i = 0; i < 24; i++) {
        s->p_min_pa[i] = NO_P;
        s->t_min_cc[i] = NO_T;
    }
    s->p_pa = -1;
    s->t_cc = NO_T;
}

void gantu_accel_push(gantu_state *s, int16_t x_mg, int16_t y_mg, int16_t z_mg)
{
    int32_t a[3] = {x_mg, y_mg, z_mg};
    uint32_t sq = 0;
    for (int i = 0; i < 3; i++) {
        int32_t a8 = a[i] * 256;
        if (!s->ema_primed) s->ema[i] = a8;
        else s->ema[i] += (a8 - s->ema[i]) / (int32_t)(1L << s->ema_shift);
        int32_t st = (s->ema[i] >= 0 ? s->ema[i] + 128 : s->ema[i] - 128) / 256;
        int32_t d = a[i] - st;
        sq += (uint32_t)(d * d);
    }
    s->ema_primed = 1;
    uint32_t v = isqrt32(sq);
    s->vedba_mg_samples += v;
    s->minute_mg_samples += v;
    s->minute_samples++;
}

static void roll_hour(gantu_state *s)
{
    for (int i = 23; i > 0; i--) {
        s->p_min_pa[i] = s->p_min_pa[i - 1];
        s->t_min_cc[i] = s->t_min_cc[i - 1];
    }
    s->p_min_pa[0] = NO_P;
    s->t_min_cc[0] = NO_T;
}

void gantu_minute_tick(gantu_state *s)
{
    int active = 0;
    if (s->minute_samples) {
        uint64_t mean = s->minute_mg_samples / s->minute_samples;
        active = mean > s->cfg.active_mg;
    }
    if (active) s->minutes_since_active = 0;
    else if (s->minutes_since_active != UINT32_MAX) s->minutes_since_active++;
    s->minute_mg_samples = 0;
    s->minute_samples = 0;

    if (++s->minute_in_hour >= 60) {
        s->minute_in_hour = 0;
        roll_hour(s);
    }
}

void gantu_env_sample(gantu_state *s, int32_t pressure_pa, int16_t temp_cc, uint16_t light_raw, uint16_t batt_mv)
{
    s->p_pa = pressure_pa;
    s->t_cc = temp_cc;
    s->light_raw = light_raw;
    s->batt_mv = batt_mv;
    if (pressure_pa >= 0 && pressure_pa < s->p_min_pa[0]) s->p_min_pa[0] = pressure_pa;
    if (temp_cc != NO_T && temp_cc < s->t_min_cc[0]) s->t_min_cc[0] = temp_cc;
}

uint32_t gantu_vedba_cum_units(const gantu_state *s)
{
    /* 0.1 g*s = 100 mg*s = 100 * odr mg-samples */
    return (uint32_t)(s->vedba_mg_samples / (100ULL * s->cfg.odr_hz));
}

uint8_t gantu_light_code(uint16_t light_raw)
{
    if (light_raw > 4095) light_raw = 4095;
    return (uint8_t)(light_raw >> 6);
}

static uint32_t clampu(int64_t v, uint32_t lo, uint32_t hi)
{
    return v < (int64_t)lo ? lo : (v > (int64_t)hi ? hi : (uint32_t)v);
}

static uint32_t temp_code(int16_t cc)
{
    if (cc == NO_T) return 255;
    /* (T + 20 degC) / 0.25 degC, rounded; 0..254 -> -20.00 .. +43.50 degC; 255 = no data */
    int32_t x = (int32_t)cc + 2000;
    if (x < 0) return 0;
    return clampu((x + 12) / 25, 0, 254);
}

static uint32_t press_code(int32_t pa)
{
    if (pa < 0 || pa == NO_P) return 8191;
    /* (P - 300 hPa) / 0.1 hPa, rounded; 0..8190 -> 300.0 .. 1119.0 hPa; 8191 = no data */
    return clampu(((int64_t)pa - 30000 + 5) / 10, 0, 8190);
}

typedef struct {
    uint8_t *buf;
    uint32_t bit;
} bitw;

static void put(bitw *w, uint32_t v, uint32_t n)
{
    for (int i = (int)n - 1; i >= 0; i--) {
        if ((v >> i) & 1u) w->buf[w->bit >> 3] |= (uint8_t)(0x80u >> (w->bit & 7));
        w->bit++;
    }
}

void gantu_pack_payload(gantu_state *s, uint8_t out[GANTU_PAYLOAD_LEN])
{
    memset(out, 0, GANTU_PAYLOAD_LEN);
    bitw w = {out, 0};

    uint32_t msa = s->minutes_since_active;
    uint32_t alive = (msa != UINT32_MAX) && (msa < (uint32_t)s->cfg.alive_window_h * 60u);
    uint32_t inactive_h = (msa == UINT32_MAX) ? 127 : clampu(msa / 60, 0, 127);

    int16_t tmin = NO_T;
    int32_t pmin = NO_P;
    uint32_t pmin_age = 31;
    for (int i = 0; i < 24; i++) {
        if (s->t_min_cc[i] < tmin) tmin = s->t_min_cc[i];
        if (s->p_min_pa[i] < pmin) {
            pmin = s->p_min_pa[i];
            pmin_age = (uint32_t)i;
        }
    }

    put(&w, GANTU_PAYLOAD_VERSION, 3);
    put(&w, alive, 1);
    put(&w, inactive_h, 7);
    put(&w, gantu_vedba_cum_units(s) & 0xFFFFFFu, 24);
    put(&w, temp_code(s->t_cc), 8);
    put(&w, temp_code(tmin), 8);
    put(&w, press_code(s->p_pa), 13);
    put(&w, press_code(pmin), 13);
    put(&w, pmin_age, 5);
    put(&w, gantu_light_code(s->light_raw), 6);
    put(&w, s->batt_mv ? clampu(((int32_t)s->batt_mv - 2000 + 25) / 50, 0, 31) : 0, 5);
    put(&w, s->msg_counter, 8);
    put(&w, 0, 3); /* reserved */
    /* w.bit == 104 */
    s->msg_counter++;
}
