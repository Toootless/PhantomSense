#ifndef WIFI_SETUP_H
#define WIFI_SETUP_H

#include "app_config.h"
#include "esp_err.h"
#include <stdbool.h>

/**
 * Initialize and connect to WiFi
 * @param config WiFi configuration
 * @param event_group FreeRTOS event group for signaling WiFi connection (opaque handle)
 * @return ESP_OK on success
 */
esp_err_t wifi_setup_init(const phantom_wifi_config_t *config, void *event_group);

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

/**
 * Get WiFi signal strength (RSSI)
 * @return RSSI in dBm (typical range: -30 to -90)
 */
int wifi_get_rssi(void);

#endif // WIFI_SETUP_H
