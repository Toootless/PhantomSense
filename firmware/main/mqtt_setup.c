#include "mqtt_setup.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "MQTT_SETUP";
static esp_mqtt_client_handle_t mqtt_client = NULL;
static bool mqtt_connected = false;
static char topic_buffer[256];

static void mqtt_event_handler(void *handler_args, esp_event_base_t base,
                              int32_t event_id, void *event_data) {
    esp_mqtt_event_handle_t event = event_data;

    switch ((esp_mqtt_event_id_t)event_id) {
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
            ESP_LOGI(TAG, "MQTT_EVENT_PUBLISHED, msg_id=%d", event->msg_id);
            break;

        case MQTT_EVENT_DATA:
            ESP_LOGI(TAG, "MQTT_EVENT_DATA");
            break;

        case MQTT_EVENT_ERROR:
            ESP_LOGE(TAG, "MQTT_EVENT_ERROR");
            break;

        default:
            ESP_LOGI(TAG, "Other event id:%d", event->event_id);
            break;
    }
}

esp_err_t mqtt_setup_init(const mqtt_config_t *config) {
    ESP_LOGI(TAG, "MQTT Setup Starting");
    
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = config->broker_uri,
        .credentials.username = config->username,
        .credentials.password = config->password,
        .keepalive = config->keepalive,
    };

    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    if (!mqtt_client) {
        ESP_LOGE(TAG, "Failed to initialize MQTT client");
        return ESP_FAIL;
    }

    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, 
                                  mqtt_event_handler, NULL);

    esp_err_t err = esp_mqtt_client_start(mqtt_client);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start MQTT client: %s", esp_err_to_name(err));
        return err;
    }

    ESP_LOGI(TAG, "MQTT client started, connecting to %s", config->broker_uri);
    return ESP_OK;
}

int mqtt_publish_message(const char *subtopic, const uint8_t *data, int len) {
    if (!mqtt_client || !mqtt_connected) {
        ESP_LOGW(TAG, "MQTT not connected");
        return -1;
    }

    snprintf(topic_buffer, sizeof(topic_buffer), "%s/%s",
            app_config_get_current()->mqtt.topic_prefix, subtopic);

    return esp_mqtt_client_publish(mqtt_client, topic_buffer, 
                                  (const char *)data, len, 1, 0);
}

int mqtt_publish_json(const char *subtopic, const char *json) {
    return mqtt_publish_message(subtopic, (const uint8_t *)json, strlen(json));
}

bool mqtt_is_connected(void) {
    return mqtt_connected;
}

esp_mqtt_client_handle_t mqtt_get_handle(void) {
    return mqtt_client;
}
