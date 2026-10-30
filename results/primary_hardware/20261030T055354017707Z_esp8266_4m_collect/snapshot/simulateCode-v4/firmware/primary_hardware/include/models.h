#pragma once
#include <math.h>
namespace m0 {
#include "ph_Persistence.h"
#undef MODEL_INPUTS
}
namespace m1 {
#include "ph_Ridge.h"
#undef MODEL_INPUTS
}
namespace m2 {
#include "ph_Forest16.h"
#undef MODEL_INPUTS
}
namespace m3 {
#include "vibrio_Mean.h"
#undef MODEL_INPUTS
}
namespace m4 {
#include "vibrio_Forest16.h"
#undef MODEL_INPUTS
}
__attribute__((noinline)) static float dispatch(int model,const double* x) { float f[10]; for(int i=0;i<10;i++)f[i]=(float)x[i]; switch(model) {
case 0:return m0::model_predict(f);
case 1:return m1::model_predict(f);
case 2:return m2::model_predict(x);
case 3:return m3::model_predict(f);
case 4:return m4::model_predict(x);
default:return NAN;} }
static void reset_models() {
m0::model_reset();
m1::model_reset();
m2::model_reset();
m3::model_reset();
m4::model_reset();
}