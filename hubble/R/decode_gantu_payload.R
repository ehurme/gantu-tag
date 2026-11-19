# Decode the 13-byte gantu Hubble payload (format v1). MIT licence.
# Base R only. Vectorised over a character vector of hex strings (26 hex characters each).
#
#   source("hubble/R/decode_gantu_payload.R")
#   df <- decode_gantu_payload(c("2fe00000f9191b58dac036a800", "23c03d60590e1b5bdaabb67cb0"))
#   df$vedba_g_s_since_prev <- gantu_vedba_diff(df$vedba_cum_counts)
#
# Format: hubble/docs/payload_v1.md. Python twin: hubble/tools/gantu_payload.py.

gantu_fields <- data.frame(
  name = c("version", "alive", "inactive_h", "vedba_cum", "temp", "temp_min24", "pressure",
           "pressure_min24", "pressure_min24_age_h", "light", "battery", "counter", "reserved"),
  bits = c(3, 1, 7, 24, 8, 8, 13, 13, 5, 6, 5, 8, 3),
  stringsAsFactors = FALSE
)
stopifnot(sum(gantu_fields$bits) == 104)

# Raw integer codes, one row per payload
unpack_gantu_payload <- function(hex) {
  hex <- tolower(trimws(as.character(hex)))
  ok <- !is.na(hex) & grepl("^[0-9a-f]{26}$", hex)
  out <- matrix(NA_real_, nrow = length(hex), ncol = nrow(gantu_fields),
                dimnames = list(NULL, gantu_fields$name))
  for (i in which(ok)) {
    bytes <- strtoi(substring(hex[i], seq(1, 25, 2), seq(2, 26, 2)), base = 16L)
    bits <- as.vector(vapply(bytes, function(b) as.integer(intToBits(b))[8:1], integer(8)))
    pos <- 1
    for (j in seq_len(nrow(gantu_fields))) {
      n <- gantu_fields$bits[j]
      out[i, j] <- sum(bits[pos:(pos + n - 1)] * 2^((n - 1):0))
      pos <- pos + n
    }
  }
  as.data.frame(out)
}

# Physical values; NA marks "no data"
decode_gantu_payload <- function(hex) {
  cd <- unpack_gantu_payload(hex)
  bad <- !is.na(cd$version) & cd$version != 1
  if (any(bad)) {
    warning(sum(bad), " payload(s) with an unknown format version set to NA")
    cd[bad, ] <- NA
  }
  na_if <- function(x, code) ifelse(x == code, NA, x)
  temp <- function(x) na_if(x, 255) * 0.25 - 20
  press <- function(x) 300 + na_if(x, 8191) * 0.1
  data.frame(
    hex                  = as.character(hex),
    version              = cd$version,
    alive                = cd$alive == 1,
    inactive_h           = na_if(cd$inactive_h, 127),       # NA = >= 127 h, or never active
    vedba_cum_counts     = cd$vedba_cum,
    vedba_cum_g_s        = cd$vedba_cum * 0.1,              # g*s; wraps at 2^24 counts
    temp_c               = temp(cd$temp),
    temp_min24_c         = temp(cd$temp_min24),
    pressure_hpa         = press(cd$pressure),
    pressure_min24_hpa   = press(cd$pressure_min24),
    pressure_min24_age_h = na_if(cd$pressure_min24_age_h, 31),
    light_code           = cd$light,                        # top 6 bits of the 12-bit ADC
    battery_v            = ifelse(cd$battery == 0, NA, 2 + cd$battery * 0.05),
    counter              = cd$counter,
    stringsAsFactors = FALSE
  )
}

# VeDBA (g*s) accumulated since the previous message of the same tag (vector in time order); first is NA.
# Handles the 24-bit wrap; multiply by 9.80665 for m/s^2 * s.
gantu_vedba_diff <- function(vedba_cum_counts) {
  d <- c(NA, diff(vedba_cum_counts))
  (d %% 2^24) * 0.1
}
