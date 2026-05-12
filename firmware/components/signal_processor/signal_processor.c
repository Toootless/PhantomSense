#include "signal_processor.h"
#include "esp_log.h"
#include <string.h>
#include <math.h>
#include <stdbool.h>

static const char *TAG = "SIGNAL_PROCESSOR";

typedef struct {
    signal_processor_config_t config;
    uint32_t frames_processed;
    bool initialized;
} signal_processor_state_t;

static signal_processor_state_t processor_state = {0};

/**
 * Calculate mean of array
 */
static float calculate_mean(const int8_t *data, uint16_t len) {
    if (!data || len == 0) return 0.0f;
    
    int32_t sum = 0;
    for (uint16_t i = 0; i < len; i++) {
        sum += data[i];
    }
    return (float)sum / len;
}

/**
 * Calculate standard deviation of array
 */
static float calculate_std(const int8_t *data, uint16_t len, float mean) {
    if (!data || len == 0) return 0.0f;
    
    float variance = 0.0f;
    for (uint16_t i = 0; i < len; i++) {
        float diff = data[i] - mean;
        variance += diff * diff;
    }
    return sqrtf(variance / len);
}

/**
 * Find maximum value in array
 */
static int8_t find_max(const int8_t *data, uint16_t len) {
    if (!data || len == 0) return 0;
    
    int8_t max = data[0];
    for (uint16_t i = 1; i < len; i++) {
        if (data[i] > max) {
            max = data[i];
        }
    }
    return max;
}

/**
 * Median filter for noise reduction
 */
static int8_t median_filter_3tap(int8_t a, int8_t b, int8_t c) {
    // Simple 3-point median
    if ((a >= b && a <= c) || (a >= c && a <= b)) return a;
    if ((b >= a && b <= c) || (b >= c && b <= a)) return b;
    return c;
}

esp_err_t signal_processor_init(const signal_processor_config_t *config) {
    if (!config) {
        return ESP_ERR_INVALID_ARG;
    }

    memcpy(&processor_state.config, config, sizeof(signal_processor_config_t));
    processor_state.frames_processed = 0;
    processor_state.initialized = true;

    ESP_LOGI(TAG, "Signal Processor initialized");
    return ESP_OK;
}

esp_err_t signal_processor_extract_features(const csi_frame_t *csi_frame,
                                           signal_features_t *features) {
    if (!processor_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    if (!csi_frame || !features) {
        return ESP_ERR_INVALID_ARG;
    }

    // Initialize features
    memset(features, 0, sizeof(signal_features_t));
    features->timestamp_ms = csi_frame->timestamp_ms;

    // Calculate statistics on amplitude
    features->amplitude_mean = calculate_mean(csi_frame->amplitude, csi_frame->len);
    features->amplitude_std = calculate_std(csi_frame->amplitude, csi_frame->len,
                                           features->amplitude_mean);
    features->amplitude_max = find_max(csi_frame->amplitude, csi_frame->len);

    // Calculate SNR (simplified)
    int8_t noise = (int8_t)csi_frame->noise_floor;
    float signal_power = features->amplitude_mean * features->amplitude_mean;
    float noise_power = noise * noise;
    features->snr = (noise_power > 0.0f) ? 10.0f * log10f(signal_power / noise_power) : 0.0f;

    // Calculate phase velocity (simplified)
    if (csi_frame->len > 1) {
        int16_t phase_diff = csi_frame->phase[csi_frame->len - 1] - csi_frame->phase[0];
        features->phase_velocity = (float)phase_diff / (float)csi_frame->len;
    }

    // Activity score based on amplitude and phase changes
    // Higher mean amplitude and phase velocity = higher activity
    float amplitude_component = (features->amplitude_mean + 128.0f) / 256.0f;  // Normalize to 0-1
    float velocity_component = fabs(features->phase_velocity) / 128.0f;         // Normalize
    features->activity_score = (uint16_t)((amplitude_component + velocity_component) * 500.0f);
    if (features->activity_score > 1000) features->activity_score = 1000;

    processor_state.frames_processed++;
    return ESP_OK;
}

esp_err_t signal_processor_apply_filter(const int8_t *input,
                                       int8_t *output,
                                       uint16_t len) {
    if (!input || !output || len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!processor_state.config.apply_median_filter) {
        memcpy(output, input, len);
        return ESP_OK;
    }

    // Apply 3-tap median filter
    output[0] = input[0];
    for (uint16_t i = 1; i < len - 1; i++) {
        output[i] = median_filter_3tap(input[i - 1], input[i], input[i + 1]);
    }
    output[len - 1] = input[len - 1];

    return ESP_OK;
}

esp_err_t signal_processor_calibrate_phase(int8_t *phase_data, uint16_t len) {
    if (!phase_data || len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!processor_state.config.apply_phase_calibration) {
        return ESP_OK;
    }

    // Simple linear phase correction based on subcarrier index
    // Compensates for phase variation due to frequency offset
    for (uint16_t i = 0; i < len; i++) {
        // Simplified phase unwrapping (actual implementation would be more complex)
        phase_data[i] = phase_data[i];  // Placeholder
    }

    return ESP_OK;
}

esp_err_t signal_processor_get_stats(uint32_t *frames_processed) {
    if (!frames_processed) {
        return ESP_ERR_INVALID_ARG;
    }

    *frames_processed = processor_state.frames_processed;
    return ESP_OK;
}

esp_err_t signal_processor_deinit(void) {
    memset(&processor_state, 0, sizeof(signal_processor_state_t));
    ESP_LOGI(TAG, "Signal Processor deinitialized");
    return ESP_OK;
}
