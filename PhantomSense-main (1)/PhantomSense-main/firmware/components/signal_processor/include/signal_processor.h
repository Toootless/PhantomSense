#ifndef SIGNAL_PROCESSOR_H
#define SIGNAL_PROCESSOR_H

#include <stdint.h>
#include <stddef.h>
#include "esp_err.h"
#include "csi_driver.h"

// Signal processing configuration
typedef struct {
    uint16_t buffer_size;           // Number of samples to buffer
    uint8_t apply_median_filter;    // Enable median filtering
    uint8_t apply_phase_calibration;// Enable phase unwrapping
    float noise_threshold;          // Noise floor threshold
} signal_processor_config_t;

// Processed features structure
typedef struct {
    uint32_t timestamp_ms;
    float amplitude_mean;           // Mean amplitude
    float amplitude_std;            // Standard deviation
    float amplitude_max;            // Maximum amplitude
    float phase_velocity;           // Phase velocity estimate
    float snr;                      // Signal-to-noise ratio
    uint16_t activity_score;        // 0-1000 activity confidence
} signal_features_t;

/**
 * Initialize signal processor
 * @param config Signal processor configuration
 * @return ESP_OK on success
 */
esp_err_t signal_processor_init(const signal_processor_config_t *config);

/**
 * Process a CSI frame and extract features
 * @param csi_frame Input CSI frame
 * @param features Output processed features
 * @return ESP_OK on success
 */
esp_err_t signal_processor_extract_features(const csi_frame_t *csi_frame,
                                           signal_features_t *features);

/**
 * Apply noise filtering to CSI amplitude data
 * @param input Input amplitude array
 * @param output Output amplitude array
 * @param len Array length
 * @return ESP_OK on success
 */
esp_err_t signal_processor_apply_filter(const int8_t *input,
                                       int8_t *output,
                                       uint16_t len);

/**
 * Calibrate phase data
 * @param phase_data Phase data to calibrate
 * @param len Array length
 * @return ESP_OK on success
 */
esp_err_t signal_processor_calibrate_phase(int8_t *phase_data, uint16_t len);

/**
 * Get processor statistics
 * @param frames_processed Total frames processed (output)
 * @return ESP_OK on success
 */
esp_err_t signal_processor_get_stats(uint32_t *frames_processed);

/**
 * Release processor resources
 * @return ESP_OK on success
 */
esp_err_t signal_processor_deinit(void);

#endif // SIGNAL_PROCESSOR_H
