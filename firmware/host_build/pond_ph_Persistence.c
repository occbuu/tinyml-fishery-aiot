#include "C:/OccBuu/Paper2026/10_AIoT_Fishery_Review/simulateCode-v4/firmware/c_reference/pond_ph_Persistence.h"
__declspec(dllexport) void reset_state(void){ model_reset(); }
__declspec(dllexport) float evaluate(const float *x){return model_predict(x);}
