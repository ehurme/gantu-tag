CFLAGS ?= -std=c99 -O2 -Wall -Wextra -Wpedantic
test_core: test_core.c ../core/gantu_core.c ../core/gantu_core.h
	$(CC) $(CFLAGS) -o $@ test_core.c ../core/gantu_core.c -lm
run: test_core
	./test_core payloads.csv
clean:
	rm -f test_core payloads.csv
.PHONY: run clean
