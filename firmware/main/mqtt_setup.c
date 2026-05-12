#include "mqtt_setup.h"
#include "esp_log.h"
#include <string.h>
#include <stddef.h>

static const char *TAG = "MQTT_SETUP";

// Global MQTT client handle and state
static esp_mqtt_client_handle_t mqtt_client = NULL;
static bool mqtt_connected = false;
static const mqtt_config_t *current_config = NULL;

/**
 * MQTT event handler
 */
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
    esp_mqtt_event_handle_t event = event_data;
    
    switch (event->event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT_EVENT_CONNECTED");
            mqtt_connected = true;
            break;
            
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGI(TAG, "MQTT_EVENT_DISCONNECTED");
            mqtt_connected = false;
            break;
            
        case MQTT_EVENT_SUBSCRIBED:
            ESP_LOGI(TAG, "MQTT_EVENT_SUBSCRIBED, msg_id=%d", event->msg_id);
            break;
            
        case MQTT_EVENT_UNSUBSCRIBED:
            ESP_LOGI(TAG, "MQTT_EVENT_UNSUBSCRIBED, msg_id=%d", event->msg_id);
            break;
            
        case MQTT_EVENT_PUBLISHED:
            ESP_LOGD(TAG, "MQTT_EVENT_PUBLISHED, msg_id=%d", event->msg_id);
            break;
            
        case MQTT_EVENT_DATA:
            ESP_LOGD(TAG, "MQTT_EVENT_DATA");
            break;
            
        case MQTT_EVENT_ERROR:
            ESP_LOGE(TAG, "MQTT_EVENT_ERROR");
            break;
            
        default:
            ESP_LOGD(TAG, "Other mqtt event id:%d", event->event_id);
            break;
    }
}

/**
 * Initialize MQTT client
 */
esp_err_t mqtt_setup_init(const mqtt_config_t *config) {
    if (!config) {
        ESP_LOGE(TAG, "NULL config");
        return ESP_ERR_INVALID_ARG;
    }
    
    current_config = config;
    
    ESP_LOGI(TAG, "Initializing MQTT client");
    ESP_LOGI(TAG, "  Broker: %s", config->broker_uri);
    ESP_LOGI(TAG, "  Topic prefix: %s", config->topic_prefix);
    
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = config->broker_uri,
        .credentials.username = "",
        .credentials.password = "",
        .network.timeout_ms = 10000,
        .network.disable_auto_reconnect = false,
    };
    
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    if (!mqtt_client) {
        ESP_LOGE(TAG, "Failed to initialize MQTT client");
        return ESP_FAIL;
    }
    
    // Register event handler
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    
    // Start the client
    esp_err_t err = esp_mqtt_client_start(mqtt_client);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start MQTT client: %s", esp_err_to_name(err));
        return err;
    }
    
    ESP_LOGI(TAG, "MQTT client started");
    return ESP_OK;
}

/**
 * Publish a message to MQTT
 */
int mqtt_publish_message(const char *subtopic, const uint8_t *data, int len) {
    if (!mqtt_client || !mqtt_connected) {
        ESP_LOGW(TAG, "MQTT not connected, dropping message");
        return -1;
    }
    
    if (!subtopic || !data || len < 0) {
        ESP_LOGE(TAG, "Invalid arguments");
        return -1;
    }
    
    // Build full topic: prefix/subtopic
    char full_topic[256];
    snprintf(full_topic, sizeof(full_topic), "%s/%s", current_config->topic_prefix, subtopic);
    
    int msg_id = esp_mqtt_client_publish(mqtt_client, full_topic, (const char *)data, len, 1, 0);
    
    if (msg_id < 0) {
        ESP_LOGW(TAG, "Failed to publish to %s", full_topic);
    } else {
        ESP_LOGD(TAG, "Published to %s (msg_id=%d, len=%d)", full_topic, msg_id, len);
    }
    
    return msg_id;
}

/**
 * Publish a JSON string to MQTT
 */
int mqtt_publish_json(const char *subtopic, const char *json) {
    if (!json) {
        ESP_LOGE(TAG, "NULL JSON");
        return -1;
    }
    
    return mqtt_publish_message(subtopic, (const uint8_t *)json, strlen(json));
}

/**
 * Check if MQTT is connected
 */
bool mqtt_is_connected(void) {
    return mqtt_connected && mqtt_client != NULL;
}

/**
 * Get MQTT client handle
 */
esp_mqtt_client_handle_t mqtt_get_handle(void) {
    return mqtt_client;
}
