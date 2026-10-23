/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 12
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos, temperature, ph, turbidity */
static const float model_median[12] = {6.882470131e+00f,6.882470131e+00f,6.881088734e+00f,6.881088734e+00f,6.881088734e+00f,6.879174709e+00f,1.143714227e-02f,1.224646853e-16f,-1.836970147e-16f,2.731690788e+01f,7.823948383e+00f,3.324119329e+00f};
static const float model_center[12] = {6.881135464e+00f,6.880726337e+00f,6.880202293e+00f,6.880026817e+00f,6.880012512e+00f,6.880343914e+00f,4.094585602e-04f,1.256321673e-03f,-2.176012844e-03f,2.732072258e+01f,7.825810432e+00f,3.321120739e+00f};
static const float model_scale[12] = {6.070674062e-01f,6.074894667e-01f,6.071267128e-01f,6.072126031e-01f,6.071974635e-01f,2.411665618e-01f,8.704328537e-01f,7.069342136e-01f,7.072748542e-01f,5.896942616e-01f,2.026007921e-01f,4.395543337e-01f};
static const float model_w[12] = {1.010680292e-02f,2.050950751e-02f,1.952692680e-02f,1.845660433e-02f,7.398826536e-03f,-5.282100663e-02f,-7.265119813e-03f,-6.431295536e-03f,-7.389615756e-03f,-4.406846128e-03f,-2.957926365e-03f,-7.145625539e-03f};
static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];
float out=6.881356628e+00f; for(int i=0;i<MODEL_INPUTS;i++) out+=x[i]*model_w[i]; return out; }
static inline void model_reset(void) {}