idf_component_register(
    SRCS "main.c" "app_config.c" "wifi_setup.c" "mqtt_setup.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_wifi esp_netif nvs_flash mqtt_client esp_event esp_system
    PRIV_REQUIRES csi_driver signal_processor log
)
