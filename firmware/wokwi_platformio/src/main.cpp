// Deterministic firmware replay plus a virtual ADC/invalid-state demonstration.
// Potentiometer voltage is NOT a qualified DO probe or chemical calibration.
// No relay or physical aerator is driven by this project.
#include <Arduino.h>
#include <math.h>
#include <esp_timer.h>
#include <esp_heap_caps.h>
#include "replay_fixture.h"

#if BENCH_MODEL == 0
#include "Ridge.h"
static const char *MODEL_NAME="Ridge";
#elif BENCH_MODEL == 1
#include "Mean.h"
static const char *MODEL_NAME="Mean";
#elif BENCH_MODEL == 2
#include "Persistence.h"
static const char *MODEL_NAME="Persistence";
#elif BENCH_MODEL == 3
#include "Tree4.h"
static const char *MODEL_NAME="Tree4";
#else
static const char *MODEL_NAME="LoopBaseline";
static void model_reset() {}
static float model_predict(const float *x) { return x[0]; }
#endif

static volatile float checksum=0;
static volatile unsigned input_index=0;

void setup() {
  Serial.begin(115200);delay(1000);pinMode(27,INPUT_PULLUP);
  Serial.printf("META,model=%s,cpu_mhz=%u,mode=firmware_replay,rows=%d\n",MODEL_NAME,getCpuFrequencyMhz(),REPLAY_ROWS);
  model_reset();unsigned failures=0;float max_error=0;
  for(unsigned i=0;i<REPLAY_ROWS;i++) {
    const float got=model_predict(replay_inputs[i]);
#if BENCH_MODEL < 4
    const float expected=replay_expected[i][BENCH_MODEL];
    const float error=fabsf(got-expected);max_error=fmaxf(max_error,error);
    if(!isfinite(got) || error>2e-4f+2e-5f*fabsf(expected)) failures++;
#endif
    if(isfinite(got)) checksum=checksum+got;
  }
  Serial.printf("PARITY,model=%s,failures=%u,max_abs_error=%.9g\n",MODEL_NAME,failures,max_error);
  Serial.println(failures ? "REPLAY_FAIL" : "REPLAY_PASS");
  // Timed block excludes UART and ADC. Simulation values must be labelled as such.
  model_reset();
  for(unsigned i=0;i<100;i++) checksum=checksum+model_predict(replay_inputs[i%REPLAY_ROWS]);
  for(unsigned block=0;block<40;block++) {
    const int64_t start=esp_timer_get_time();
    for(unsigned i=0;i<1000;i++) {
      input_index=(i+block)%REPLAY_ROWS;
      const float y=model_predict(replay_inputs[input_index]);
      if(isfinite(y)) checksum=checksum+y;
    }
    const int64_t elapsed=esp_timer_get_time()-start;
    Serial.printf("BLOCK,model=%s,id=%u,calls=1000,elapsed_us=%lld\n",MODEL_NAME,block,(long long)elapsed);
    delay(1);
  }
  Serial.printf("MEMORY,model=%s,free_heap_bytes=%u,min_free_heap_bytes=%u,stack_high_water_raw=%u\n",
    MODEL_NAME,(unsigned)heap_caps_get_free_size(MALLOC_CAP_8BIT),
    (unsigned)heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT),(unsigned)uxTaskGetStackHighWaterMark(NULL));
  Serial.println("BENCHMARK_DONE");
}

void loop() {
  // Independent virtual protection demonstration, outside forecast timing.
  const bool invalid=digitalRead(27)==LOW;
  const float virtual_do=analogRead(34)*(10.0f/4095.0f);
  const bool protection_request=invalid || virtual_do<3.0f;
  Serial.printf("VIRTUAL_INPUT,do_demo=%.3f,quality=%s,protection_request=%d\n",
    virtual_do,invalid?"UNKNOWN":"DEMO_ONLY",protection_request);
  delay(1000);
}
