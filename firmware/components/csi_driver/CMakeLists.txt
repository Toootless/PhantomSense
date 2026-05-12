idf_component_register(
    SRCS "csi_driver.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_wifi esp_netif esp_event esp_system esp_timer
)
