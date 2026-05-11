#ifndef CSI_DRIVER_H
#define CSI_DRIVER_H

#include <stdint.h>
#include <stddef.h>
#include "esp_err.h"

// CSI Frame structure
typedef struct {
    uint32_t timestamp_ms;          // Timestamp in milliseconds
    uint8_t mac[6];                 // Source MAC address
    uint8_t rssi;                   // Receive Signal Strength Indicator
    uint8_t noise_floor;            // Noise floor estimate
    uint16_t len;                   // Number of subcarriers
    int8_t *amplitude;              // CSI amplitude per subcarrier
    int8_t *phase;                  // CSI phase per subcarrier
} csi_frame_t;

// CSI configuration structure
typedef struct {
    uint32_t sampling_rate_hz;      // Target sampling rate (Hz)
    uint16_t buffer_size;           // Number of frames to buffer
    uint8_t apply_filtering;        // Apply median filter
    uint8_t rx_only_mode;           // Monitor incoming packets only
} csi_driver_config_t;

// CSI callback function type
typedef void (*csi_callback_t)(const csi_frame_t *frame);

/**
 * Initialize CSI driver
 * @param config CSI driver configuration
 * @return ESP_OK on success
 */
esp_err_t csi_driver_init(const csi_driver_config_t *config);

/**
 * Start CSI data acquisition
 * @return ESP_OK on success
 */
esp_err_t csi_driver_start(void);

/**
 * Stop CSI data acquisition
 * @return ESP_OK on success
 */
esp_err_t csi_driver_stop(void);

/**
 * Register a callback to be called when CSI frame is available
 * @param callback Function to call
 * @return ESP_OK on success
 */
esp_err_t csi_driver_register_callback(csi_callback_t callback);

/**
 * Get the latest CSI frame (non-blocking)
 * @param frame Pointer to frame structure to fill
 * @return ESP_OK if frame available, ESP_ERR_INVALID_STATE if not
 */
esp_err_t csi_driver_get_latest_frame(csi_frame_t *frame);

/**
 * Get the number of buffered frames
 * @return Number of frames in buffer
 */
uint32_t csi_driver_get_buffer_count(void);

/**
 * Get driver statistics
 * @param total_frames Total frames received (output)
 * @param dropped_frames Dropped frames due to buffer overflow (output)
 * @return ESP_OK on success
 */
esp_err_t csi_driver_get_stats(uint32_t *total_frames, uint32_t *dropped_frames);

/**
 * Release CSI driver resources
 * @return ESP_OK on success
 */
esp_err_t csi_driver_deinit(void);

#endif // CSI_DRIVER_H
