/* ESP-IDF measurement scaffold. Not a pond controller or measured benchmark.
 * Copy ONE generated task header as model.h; supply the exact causal feature
 * vector from its export reference. No Wi-Fi/cloud/relay dependency is required.
 */
#include <cstdio>
#include <cmath>
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "model.h"

extern "C" void app_main(void) {
    float input[MODEL_INPUTS] = {0};
    // Replace with the recorded fixture or qualified feature acquisition.
    volatile float checksum = 0;
    for (int k=0;k<20;k++) checksum += model_predict(input);
    const int n=1000;
    const int64_t start=esp_timer_get_time();
    for (int k=0;k<n;k++) checksum += model_predict(input);
    const int64_t elapsed=esp_timer_get_time()-start;
    std::printf("model_inputs,mean_inference_us,min_free_heap_bytes,checksum\n");
    std::printf("%d,%.6f,%u,%.9g\n",MODEL_INPUTS,double(elapsed)/n,
        unsigned(heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT)),double(checksum));
    // Record chip, clock, firmware hash, compiler, model and full feature path.
    // Heap minima do not measure static SRAM, stack high-water or total node power.
}
