/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 10
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos, salinity */
static const float model_median[10] = {1.258215046e+01f,1.258069992e+01f,1.257999992e+01f,1.257935047e+01f,1.257845020e+01f,1.257924175e+01f,-2.649999922e-03f,1.224646853e-16f,-1.836970147e-16f,3.437099838e+01f};
static const float model_center[10] = {1.257852077e+01f,1.257702065e+01f,1.257550144e+01f,1.257400036e+01f,1.256950760e+01f,1.257476139e+01f,1.499825274e-03f,1.586523023e-03f,-4.673746414e-03f,3.433474731e+01f};
static const float model_scale[10] = {1.053473711e+00f,1.052617311e+00f,1.051739454e+00f,1.050870180e+00f,1.048007965e+00f,1.048825622e+00f,6.575035304e-02f,7.076357603e-01f,7.065601945e-01f,2.501059175e-01f};
static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];
if(x[0]<=-4.178611934e-02f){if(x[5]<=-7.929847836e-01f){if(x[0]<=-1.240439653e+00f){if(x[0]<=-1.400386691e+00f){return 1.102587672e+01f;}else{return 1.118415082e+01f;}}else{if(x[0]<=-1.019931078e+00f){return 1.138684974e+01f;}else{return 1.161540534e+01f;}}}else{if(x[0]<=-3.484382778e-01f){if(x[0]<=-5.315467715e-01f){return 1.191201783e+01f;}else{return 1.213001458e+01f;}}else{if(x[0]<=-1.889658719e-01f){return 1.232279806e+01f;}else{return 1.248052597e+01f;}}}}else{if(x[0]<=1.290995061e+00f){if(x[0]<=5.346401930e-01f){if(x[0]<=1.834212020e-01f){return 1.264680620e+01f;}else{return 1.292624927e+01f;}}else{if(x[0]<=8.945447803e-01f){return 1.330573495e+01f;}else{return 1.373816026e+01f;}}}else{if(x[0]<=2.096188426e+00f){if(x[0]<=1.683411121e+00f){return 1.418962368e+01f;}else{return 1.460081111e+01f;}}else{if(x[0]<=2.462785125e+00f){return 1.504174578e+01f;}else{return 1.525874286e+01f;}}}}}
static inline void model_reset(void) {}