/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 10
/* Temp, pH, DO, Sal, Alk, N-NO2-, N-NH4+, P-PO43-, TSS, COD */
static inline void model_reset(void) {}
static inline float model_predict(const float *raw) { (void)raw; return 3.031670170e+00f; }