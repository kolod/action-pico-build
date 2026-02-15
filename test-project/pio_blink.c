#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "blink.pio.h"

static void blink_program_init(PIO pio, uint sm, uint offset, uint pin, float clkdiv) {
    pio_sm_config c = blink_program_get_default_config(offset);
    sm_config_set_set_pins(&c, pin, 1);
    pio_gpio_init(pio, pin);
    pio_sm_set_consecutive_pindirs(pio, sm, pin, 1, true);
    sm_config_set_clkdiv(&c, clkdiv);
    pio_sm_init(pio, sm, offset, &c);
    pio_sm_set_enabled(pio, sm, true);
}

int main() {
    const uint LED_PIN = 25; // On-board LED on the Pico
    const float CLKDIV = 64.0f; // Slow down the state machine clock for visible blinking

    PIO pio = pio0;
    const uint sm = 0;
    const uint offset = pio_add_program(pio, &blink_program);

    blink_program_init(pio, sm, offset, LED_PIN, CLKDIV);

    // Compute on/off cycle counts for ~1 Hz blink at clkdiv 64
    // System clock ~125 MHz -> SM clock ~1.95 MHz -> 0.5s ≈ 976,000 cycles
    const uint32_t on_cycles = 976000;
    const uint32_t off_cycles = 976000;

    // Load the on/off durations into the PIO state machine (blocks until TX FIFO has room)
    pio_sm_put_blocking(pio, sm, on_cycles);
    pio_sm_put_blocking(pio, sm, off_cycles);

    // Nothing else to do; PIO handles blinking autonomously
    while (true) {
        tight_loop_contents();
    }
}
