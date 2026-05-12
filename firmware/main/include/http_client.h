#ifndef HTTP_CLIENT_H
#define HTTP_CLIENT_H

#include "app_config.h"
#include "esp_err.h"
#include "esp_http_client.h"
#include <stdbool.h>

/**
 * Initialize HTTP client for hub communication
 * 
 * @param config Pointer to http_config_t configuration
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t http_client_init(const http_config_t *config);

/**
 * Publish device update with sensor data
 * 
 * @param unit_id Unique device ID
 * @param unit_name Device name
 * @param rssi WiFi signal strength
 * @param ip_address Device IP address
 * @param csi_amplitude CSI signal amplitude
 * @param csi_noise_floor CSI noise floor value
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t http_publish_device_update(uint32_t unit_id, const char *unit_name,
                                     int rssi, const char *ip_address,
                                     float csi_amplitude, float csi_noise_floor);

/**
 * Publish JSON data via HTTP POST
 * 
 * @param json_data JSON string to send
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t http_publish_json(const char *json_data);

/**
 * Check if HTTP client is ready
 * 
 * @return true if ready, false otherwise
 */
bool http_is_ready(void);

/**
 * Get HTTP client handle
 * 
 * @return esp_http_client_handle_t handle
 */
esp_http_client_handle_t http_get_handle(void);

/**
 * Cleanup HTTP client
 * 
 * @return ESP_OK on success
 */
esp_err_t http_client_deinit(void);

#endif // HTTP_CLIENT_H
