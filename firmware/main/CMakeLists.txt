idf_component_register(
    SRCS "main.c" "app_config.c" "wifi_setup.c" "http_client.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_wifi esp_netif nvs_flash esp_http_client esp_event esp_system esp_timer
    PRIV_REQUIRES csi_driver signal_processor display_driver log
)
