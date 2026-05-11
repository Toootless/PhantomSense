#ifndef MQTT_SETUP_H
#define MQTT_SETUP_H

#include "app_config.h"
#include "esp_err.h"
#include "mqtt_client.h"

/**
 * Initialize MQTT client
 * @param config MQTT configuration
 * @return ESP_OK on success
 */
esp_err_t mqtt_setup_init(const mqtt_config_t *config);

/**
 * Publish a message to MQTT
 * @param subtopic Subtopic relative to configured prefix
 * @param data Message data
 * @param len Length of message
 * @return message ID or -1 on error
 */
int mqtt_publish_message(const char *subtopic, const uint8_t *data, int len);

/**
 * Publish a JSON string to MQTT
 * @param subtopic Subtopic relative to configured prefix
 * @param json JSON string
 * @return message ID or -1 on error
 */
int mqtt_publish_json(const char *subtopic, const char *json);

/**
 * Check if MQTT is connected
 * @return true if connected, false otherwise
 */
bool mqtt_is_connected(void);

/**
 * Get MQTT client handle
 * @return mqtt_client_handle_t
 */
esp_mqtt_client_handle_t mqtt_get_handle(void);

#endif // MQTT_SETUP_H
