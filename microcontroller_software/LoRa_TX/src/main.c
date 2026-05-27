/*
 * Copyright (c) 2019 Manivannan Sadhasivam
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/device.h>
#include <zephyr/drivers/lora.h>
#include <errno.h>
#include <zephyr/sys/util.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

#define DEFAULT_RADIO_NODE DT_ALIAS(lora0)

#define MAX_DATA_LEN 12

#define LOG_LEVEL CONFIG_LOG_DEFAULT_LEVEL
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(lora_send);

char data[MAX_DATA_LEN] = {'h', 'e', 'l', 'l', 'o', 'w', 'o', 'r', 'l', 'd', ' ', '0'};

#define LORA_EN_NODE DT_ALIAS(lora_en_pin)
static const struct gpio_dt_spec lora_en = GPIO_DT_SPEC_GET(LORA_EN_NODE, gpios);

int main(void)
{
	gpio_pin_configure_dt(&lora_en, GPIO_OUTPUT_ACTIVE);
	gpio_pin_set_dt(&lora_en, 1);
	k_msleep(100);

	const struct device *const lora_dev = DEVICE_DT_GET(DEFAULT_RADIO_NODE);
	struct lora_modem_config config;
	int ret;

	if (!device_is_ready(lora_dev)) {
		LOG_ERR("%s Device not ready", lora_dev->name);
		return 0;
	}

	config.frequency = 433000000;
	config.bandwidth = BW_125_KHZ;
	config.datarate = SF_6;
	config.preamble_len = 16;
	config.coding_rate = CR_4_5;
	config.iq_inverted = false;
	config.public_network = false; // false is 0x12, true is 0x34
	config.tx_power = 20;
	config.tx = true;

	ret = lora_config(lora_dev, &config);
	if (ret < 0) {
		LOG_ERR("LoRa config failed");
		return 0;
	}

	while (1) {
		ret = lora_send(lora_dev, data, MAX_DATA_LEN);
		
		if (ret < 0) {
			LOG_ERR("LoRa send failed");
			return 0;
		}

		LOG_INF("Data sent %c!", data[MAX_DATA_LEN - 1]);

		/* Send data at 1s interval */
		k_sleep(K_MSEC(1000));

		/* Increment final character to differentiate packets */
		if (data[MAX_DATA_LEN - 1] == '9') {
			data[MAX_DATA_LEN - 1] = '0';
		} else {
			data[MAX_DATA_LEN - 1] += 1;
		}
	}
	return 0;
}
