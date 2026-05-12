#include "wifi_setup.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "freertos/event_groups.h"
#include <string.h>

static const char *TAG = "WIFI_SETUP";
static int retry_num = 0;
static bool wifi_connected = false;
static char ip_address[16] = {0};
static void *g_event_group = NULL;

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                              int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (retry_num < *(int *)arg) {
            esp_wifi_connect();
            retry_num++;
            ESP_LOGI(TAG, "retry to connect to the AP");
        } else {
            ESP_LOGE(TAG, "Failed to connect to AP");
            wifi_connected = false;
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        esp_ip4addr_ntoa(&event->ip_info.ip, ip_address, sizeof(ip_address));
        ESP_LOGI(TAG, "got ip: %s", ip_address);
        retry_num = 0;
        wifi_connected = true;
        if (g_event_group) {
            xEventGroupSetBits(g_event_group, BIT0);
            ESP_LOGI(TAG, "WiFi connected event signaled to system");
        }
    }
}

esp_err_t wifi_setup_init(const phantom_wifi_config_t *config, void *event_group) {
    g_event_group = event_group;
    ESP_LOGI(TAG, "WiFi Setup Starting");
    
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        &config->max_retry,
                                                        &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &wifi_event_handler,
                                                        &config->max_retry,
                                                        &instance_got_ip));

    wifi_config_t wifi_config = {
        .sta = {
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
            .pmf_cfg = {
                .capable = true,
                .required = false
            },
        },
    };
    
    strcpy((char *)wifi_config.sta.ssid, config->ssid);
    strcpy((char *)wifi_config.sta.password, config->password);

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "wifi_init_sta finished.");
    return ESP_OK;
}

bool wifi_is_connected(void) {
    return wifi_connected;
}

const char* wifi_get_ip_address(void) {
    return ip_address;
}

int wifi_get_rssi(void) {
    if (!wifi_connected) {
        return 0;
    }
    
    wifi_ap_record_t ap_info;
    esp_err_t err = esp_wifi_sta_get_ap_info(&ap_info);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to get AP info: %s", esp_err_to_name(err));
        return 0;
    }
    
    return ap_info.rssi;  // dBm
}
