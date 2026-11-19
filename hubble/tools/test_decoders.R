# Cross-check the R decoder against the C core's payloads and the Python decoder's output.
args <- commandArgs(trailingOnly = TRUE)
here <- if (length(args) >= 2) args[2] else "hubble"
source(file.path(here, "R", "decode_gantu_payload.R"))
ref <- read.csv(if (length(args) >= 1) args[1] else file.path(here, "firmware/test/payloads.csv"),
                colClasses = c(hex = "character"))
d <- decode_gantu_payload(ref$hex)
ok <- c(
  alive   = all(d$alive == (ref$alive == 1)),
  vedba   = all(d$vedba_cum_counts == ref$vedba_units),
  temp    = all(abs(d$temp_c - ref$t_cc / 100) <= 0.125 + 1e-9),
  press   = all(abs(d$pressure_hpa - ref$p_pa / 100) <= 0.05 + 1e-9),
  batt    = all(abs(d$battery_v - ref$batt_mv / 1000) <= 0.025 + 1e-9),
  counter = all(diff(d$counter) %% 256 == 1),
  wrap    = isTRUE(all.equal(gantu_vedba_diff(c(2^24 - 10, 5)), c(NA, 1.5)))
)
print(ok)
cat(nrow(d), "payloads decoded in R\n")
if (!all(ok)) quit(status = 1)
