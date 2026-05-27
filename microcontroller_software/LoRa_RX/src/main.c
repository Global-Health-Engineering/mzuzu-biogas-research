/*
 * Copyright (c) 2019 Manivannan Sadhasivam
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/device.h>
#include <zephyr/drivers/lora.h>
#include <zephyr/drivers/gpio.h>
#include <errno.h>
#include <zephyr/sys/util.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/kernel.h>
#include <zephyr/toolchain.h>
#include <zephyr/sys/reboot.h>

//#include <cmsis_core.h>

#define LORA_NODE DT_ALIAS(lora0)


#define MAX_DATA_LEN 255

#define LOG_LEVEL CONFIG_LOG_DEFAULT_LEVEL
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(lora_receive);


#define LORA_EN_NODE DT_ALIAS(lora_en_pin)
static const struct gpio_dt_spec lora_en = GPIO_DT_SPEC_GET(LORA_EN_NODE, gpios);

// LORA RESET PIN
//#define LORA_RESET_NODE DT_ALIAS(lora_reset_pin)
//static const struct gpio_dt_spec lora_reset = GPIO_DT_SPEC_GET(LORA_RESET_NODE, gpios);

int main(void)
{
	gpio_pin_configure_dt(&lora_en, GPIO_OUTPUT_ACTIVE);
	gpio_pin_set_dt(&lora_en, 1);
	k_msleep(2000);

	const struct device *const lora_dev = DEVICE_DT_GET(LORA_NODE);
	struct lora_modem_config config;
	int ret, len;
	uint8_t data[24] = {0};
	int16_t rssi;
	int8_t snr;

	if (!device_is_ready(lora_dev)) {
		LOG_ERR("%s Device not ready", lora_dev->name);
		return 0;
	}


	

	while(1){
		gpio_pin_set_dt(&lora_en, 1);
		k_msleep(2000);

		config.frequency = 433000000;
		config.bandwidth = BW_125_KHZ;
		config.datarate = SF_10;
		config.preamble_len = 8;
		config.coding_rate = CR_4_5;
		config.iq_inverted = false;
		config.public_network = false; // false is 0x12, true is 0x34
		config.tx_power = 14;
		config.tx = false;

		ret = lora_config(lora_dev, &config);
		if (ret < 0) {
			LOG_ERR("LoRa config failed");
			return 0;
		}

		k_msleep(500);
		
		/* Block until data arrives */
		len = -1;
		while(len < 0){
			len = lora_recv(lora_dev, data, 24, K_FOREVER,
					&rssi, &snr);
		}
		
		if (len > 0) {
			//printk("LoRa receive successful\n");
		}


		const uint8_t *p = data;

		uint32_t battery_voltage_mv   = sys_get_le32(&p[0]);
		uint32_t tank_temp_top_mcelsius   = sys_get_le32(&p[4]);
		uint32_t tank_temp_start_mcelsius = sys_get_le32(&p[8]);
		uint32_t tank_temp_bottom_mcelsius   = sys_get_le32(&p[12]);
		uint32_t tank_temp_end_mcelsius   = sys_get_le32(&p[16]);
		uint32_t die_temp_mcelsius = sys_get_le32(&p[20]);
		

		printf("%u %u %u %u %u %u\n",
			battery_voltage_mv, tank_temp_top_mcelsius, tank_temp_start_mcelsius, tank_temp_bottom_mcelsius, tank_temp_end_mcelsius, die_temp_mcelsius);
		//printf("%u ", v_battery);
		//printf("%u ", temperature_die);
		//printf("%u ", tank_temperature_start);
		//printf("%u ", loop_counter);
		//printf("%u ", tank_temperature_end);
		//printf("%u ", tank_temperature_bottom);
		//printf("%u\n", tank_temperature_top);
		//LOG_INF("LoRa RX RSSI: %d dBm, SNR: %d dB", rssi, snr);
		//LOG_HEXDUMP_INF(data, len, "LoRa RX payload");
		
		gpio_pin_set_dt(&lora_en, 0);
		//k_msleep(1000*4*60 + 1000*30);
		k_msleep(1000*2*60);


		/*
		// Reset LoRa Module
		gpio_pin_set_dt(&lora_reset, 0);
		k_msleep(100);
		gpio_pin_set_dt(&lora_reset, 1);
		k_msleep(100);
		*/
		
	}

	return 0;
}