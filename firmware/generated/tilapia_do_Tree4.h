/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 12
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos, temperature, ph, turbidity */
static const float model_median[12] = {6.882470131e+00f,6.882470131e+00f,6.881088734e+00f,6.881088734e+00f,6.881088734e+00f,6.879174709e+00f,1.143714227e-02f,1.224646853e-16f,-1.836970147e-16f,2.731690788e+01f,7.823948383e+00f,3.324119329e+00f};
static const float model_center[12] = {6.881135464e+00f,6.880726337e+00f,6.880202293e+00f,6.880026817e+00f,6.880012512e+00f,6.880343914e+00f,4.094585602e-04f,1.256321673e-03f,-2.176012844e-03f,2.732072258e+01f,7.825810432e+00f,3.321120739e+00f};
static const float model_scale[12] = {6.070674062e-01f,6.074894667e-01f,6.071267128e-01f,6.072126031e-01f,6.071974635e-01f,2.411665618e-01f,8.704328537e-01f,7.069342136e-01f,7.072748542e-01f,5.896942616e-01f,2.026007921e-01f,4.395543337e-01f};
static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];
if(x[5]<=1.063967288e+00f){if(x[9]<=-1.425438523e+00f){if(x[0]<=-8.620249629e-01f){if(x[0]<=-1.202332616e+00f){return 7.195524165e+00f;}else{return 7.637633240e+00f;}}else{if(x[7]<=1.293924212e+00f){return 7.018094588e+00f;}else{return 6.464561185e+00f;}}}else{if(x[9]<=-5.361992121e-01f){if(x[1]<=-1.986842677e-01f){return 6.733108157e+00f;}else{return 6.877816947e+00f;}}else{if(x[5]<=9.529835582e-01f){return 6.899534286e+00f;}else{return 7.170286403e+00f;}}}}else{if(x[4]<=1.759586930e+00f){if(x[5]<=1.112130284e+00f){if(x[2]<=8.114417084e-02f){return 6.710373146e+00f;}else{return 6.358526829e+00f;}}else{if(x[11]<=1.181478739e+00f){return 6.861304853e+00f;}else{return 6.615587271e+00f;}}}else{return 6.374181764e+00f;}}}
static inline void model_reset(void) {}