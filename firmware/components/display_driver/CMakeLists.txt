idf_component_register(
    SRCS "display_driver.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_common esp_driver_gpio esp_driver_ledc esp_driver_spi freertos hal
)
