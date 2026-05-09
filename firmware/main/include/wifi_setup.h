#ifndef WIFI_SETUP_H
#define WIFI_SETUP_H

#include "app_config.h"
#include "esp_err.h"

/**
 * Initialize and connect to WiFi
 * @param config WiFi configuration
 * @return ESP_OK on success
 */
esp_err_t wifi_setup_init(const wifi_config_t *config);

/**
 * Check if WiFi is connected
 * @return true if connected, false otherwise
 */
bool wifi_is_connected(void);

/**
 * Get the local IP address
 * @return IP address as string (static buffer)
 */
const char* wifi_get_ip_address(void);

#endif // WIFI_SETUP_H
