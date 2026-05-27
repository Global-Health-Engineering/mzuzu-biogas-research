/*
 * Copyright (c) 2019 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/pm/device_runtime.h>
#include <zephyr/pm/pm.h>

#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/drivers/lora.h>
#include <zephyr/drivers/counter.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/w1.h>
#include <zephyr/drivers/sensor/w1_sensor.h>
#include <zephyr/drivers/adc.h> 

#include <zephyr/sys/util.h>
#include <zephyr/sys/byteorder.h>


// Here is a description of what this program will do:
// It will mostly be asleep. Every 5 minutes it will wake up, measure the
// temperature(s), activate the valve if necessary (remember how long it
// opened that for), and send a LoRa packet with the temperature(s) and
// valve opening duration. After sending this LoRa packet, it might get
// a reply packet with new settings.




//---------------------------- DEFINES ----------------------------------------
// comment out this line to disable debug prints
#define DEBUGGING 1

// kinds of algorithms:
// 1: simple threshold-based control
// 2: ERT calculating control
#define CONTROL_ALGORITHM 1

// this defines the maximum length of a LoRa packet
#define LORA_MAX_PACKET_LEN 32

#define NUMBER_OF_TEMP_SENSORS 3

#define PWM_PHASE_FREQUENCY 250
#define PWM_TIMER_FREQUENCY 1000000

#if !DT_NODE_EXISTS(DT_PATH(zephyr_user)) || \
	!DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
#error "No suitable devicetree overlay specified"
#endif

#define DT_SPEC_AND_COMMA(node_id, prop, idx) \
	ADC_DT_SPEC_GET_BY_IDX(node_id, idx),
//------------------------ DEVICETREE INSTANCES -------------------------------

// LORA RADIO
#define LORA_NODE DT_ALIAS(lora0)
const struct device *const lora_dev = DEVICE_DT_GET(LORA_NODE);

// ONBOARD LEDs
#define LED_RED_NODE DT_ALIAS(led_red_pin)
static const struct gpio_dt_spec led_red = GPIO_DT_SPEC_GET(LED_RED_NODE, gpios);

#define LED_GREEN_NODE DT_ALIAS(led_green_pin)
static const struct gpio_dt_spec led_green = GPIO_DT_SPEC_GET(LED_GREEN_NODE, gpios);

// LORA RESET PIN
#define LORA_RESET_NODE DT_ALIAS(lora_reset_pin)
static const struct gpio_dt_spec lora_reset = GPIO_DT_SPEC_GET(LORA_RESET_NODE, gpios);

// CONSOLE UART
const struct device* const usart1_dev = DEVICE_DT_GET(DT_NODELABEL(usart1));

// COUNTER
const struct device *counter_dev = DEVICE_DT_GET(DT_NODELABEL(counter2));

// PWM
static const struct pwm_dt_spec pwm_dev = PWM_DT_SPEC_GET(DT_NODELABEL(pwmvalve));

// ADC (for battery voltage measurement)
static const struct adc_dt_spec adc_channels[] = {
	DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), io_channels,
			     DT_SPEC_AND_COMMA)
};

// DIE TEMPERATURE
#define DIE_TEMP_NODE DT_ALIAS(die_temp0)
static const struct device *const die_temp_sensor = DEVICE_DT_GET(DIE_TEMP_NODE);

// VALVE IO
uint32_t pwm_period_in_ns = PWM_TIMER_FREQUENCY / PWM_PHASE_FREQUENCY;

//----------------------- USERSPACE VARIABLES ---------------------------------
uint8_t lora_tx_buffer[LORA_MAX_PACKET_LEN];
uint8_t lora_rx_buffer[LORA_MAX_PACKET_LEN];


// LORA config
struct lora_modem_config lora_configuration = {
	// these have to match the gateway settings!
	.frequency = 433000000,
	.bandwidth = BW_125_KHZ,
	.datarate = SF_10,
	.preamble_len = 8,
	.coding_rate = CR_4_5,
	.iq_inverted = false,
	.public_network = false,
	.tx_power = 20,
	.tx = true
};

// simple variable to hold return values
int ret;

volatile uint32_t one_second_counter = 0;
uint32_t counter_frequency;
uint16_t counter_top_value;
struct counter_alarm_cfg alarm_cfg;


// ADC variables
uint16_t adc_measurement_buffer;
struct adc_sequence sequence = {
	.buffer = &adc_measurement_buffer,
	/* buffer size in bytes, not number of samples */
	.buffer_size = sizeof(adc_measurement_buffer),
};
int32_t val_mv;
uint32_t battery_voltage_mv;

// die temperature variables
struct sensor_value die_temp;
float die_temp_celsius;

// tank temperature measurement variables
#define NUMBER_OF_TEMPERATURE_SENSORS 3
const struct device* temp_sensor_devices[NUMBER_OF_TEMPERATURE_SENSORS];
struct sensor_value temp;
struct w1_rom w1_roms[NUMBER_OF_TEMPERATURE_SENSORS];
struct sensor_value rom_values[NUMBER_OF_TEMPERATURE_SENSORS];
uint64_t rom_addresses[NUMBER_OF_TEMPERATURE_SENSORS] = {
	// TODO: THESE ARE TEMPORARY
	0x28f8a2bb00000078, // top
	0x282091c0000000eb, // middle
	0x28a91e470000006c // botttom
};
double tank_temperatures[NUMBER_OF_TEMP_SENSORS];


// control variables
#if CONTROL_ALGORITHM == 1
double tank_temperature_threshold = 70;
#endif

#if CONTROL_ALGORITHM == 2
// we need a large array of doubles to hold the ERT history
// there should be enough to look through the night?
float ert_history[128]; 
uint8_t ert_history_index = 0;
#endif



//------------------------ FUNCTION DEFINITIONS ----------------------------------

// kernel sleep forces the system to enter some power
// saving mode, use this delay instead if you don't want that
// but we do want to save power so do not use this function
static inline void blocking_sleep_ms(uint32_t ms_amount){
	uint32_t increments = ms_amount*1000*300/38;
    for(uint32_t i = 0; i < increments; i++);
}


static void counter_interrupt_callback(const struct device *dev,
                                       void *user_data) {
  // 1 second has elapsed
  one_second_counter++;
  #ifdef DEBUGGING
  //printk("Counter interrupt callback called! one_second_counter = %u\n", one_second_counter);
  #endif
}


#if CONTROL_ALGORITHM == 2
double calculate_ert(double current_temp){
	// some stuff with logarithms. The calculation is in my notebook
}
#endif

//---------------------------- MAIN FUNCTION -----------------------------------
int main(void)
{
	// CONFIGURE PERIPHERALS
	ret = pwm_set_dt(&pwm_dev, pwm_period_in_ns, 0); // turn off PWM
	gpio_pin_configure_dt(&led_red, GPIO_OUTPUT_ACTIVE);
	gpio_pin_configure_dt(&led_green, GPIO_OUTPUT_ACTIVE);
	k_msleep(1000); // wait for things to stabilize

	// DEVICE BINDINGS (TEMPERATURE SENSORS)
	temp_sensor_devices[0] =  device_get_binding("SENSOR_DS18B20_0");
	temp_sensor_devices[1] =  device_get_binding("SENSOR_DS18B20_1");
	temp_sensor_devices[2] =  device_get_binding("SENSOR_DS18B20_2");

	for(int i = 0; i < NUMBER_OF_TEMP_SENSORS; i++){
		if (!temp_sensor_devices[i] || !device_is_ready(temp_sensor_devices[i])) {
			#ifdef DEBUGGING
			printk("DS18B20 sensor device %d is not ready or found.\n", i);
			#endif
			return -1;
		}
	}

	for (int i = 0; i < NUMBER_OF_TEMP_SENSORS; i++) {
		w1_uint64_to_rom(rom_addresses[i], &w1_roms[i]);
		w1_rom_to_sensor_value(&w1_roms[i], &rom_values[i]);
	}


	// ADC SETUP
	if (!adc_is_ready_dt(&adc_channels[0])) {
		#ifdef DEBUGGING
		printk("ADC controller device %s not ready\n", adc_channels[0].dev->name);
		#endif
	}

	ret = adc_channel_setup_dt(&adc_channels[0]);
	if (ret < 0) {
		#ifdef DEBUGGING
		printk("Could not setup ADC channel (%d)\n", ret);
		#endif
	}


	while(1){
		#ifdef DEBUGGING
		printk("Program has arrived at main\n");
		#endif


		// COUNTER INIT
		one_second_counter = 0;
		counter_frequency = counter_get_frequency(counter_dev);
		
		struct counter_top_cfg counter_cfg;
		counter_cfg.ticks = counter_frequency*1; // 1 second tops
		counter_cfg.callback = counter_interrupt_callback;
		counter_cfg.flags = 0;
		counter_cfg.user_data = NULL;
		ret = counter_set_top_value(counter_dev, &counter_cfg);
		if (ret != 0) {
			#ifdef DEBUGGING
			printk("Error %d setting counter top value\n", ret);
			#endif
		}
		
		counter_start(counter_dev);
		#ifdef DEBUGGING
		printk("Counter started\n");
		#endif
		// ENDOF: COUNTER INIT


		// LED initialization
		gpio_pin_set_dt(&led_red, 1);


		// GET BATTERY VOLTAGE

		(void)adc_sequence_init_dt(&adc_channels[0], &sequence);
		ret = adc_read_dt(&adc_channels[0], &sequence);
		if (ret < 0) {
			#ifdef DEBUGGING
			printk("Could not read (%d)\n", ret);
			#endif
		}

		val_mv = (int32_t)((int16_t)adc_measurement_buffer);
		ret = adc_raw_to_millivolts_dt(&adc_channels[0],&val_mv);

		if (ret < 0) {
			#ifdef DEBUGGING
			printk(" (value in mV not available)\n");
			#endif
		} else {
			float ratio = (12200.0f / 2200.0f); // voltage divider ratio
			battery_voltage_mv = (uint32_t)((float)val_mv * ratio);
			//battery_voltage_mv = battery_voltage_mv * 13.24/13.04; // calibration factor
			#ifdef DEBUGGING
			printk("Battery voltage reading: %d mV\n", battery_voltage_mv);
			#endif
		}
		// ENDOF: GET BATTERY VOLTAGE

		// GET DIE TEMPERATURE
		ret = sensor_sample_fetch(die_temp_sensor);
		if (ret != 0) {
			#ifdef DEBUGGING
			printk("sample_fetch() failed for die temp sensor: %d\n", ret);
			k_msleep(100);
			#endif
		}

		ret = sensor_channel_get(die_temp_sensor, SENSOR_CHAN_DIE_TEMP, &die_temp);
		if (ret != 0) {
			#ifdef DEBUGGING
			printk("channel_get() failed for die temp sensor: %d\n", ret);
			k_msleep(100);
			#endif
		}
		
		die_temp_celsius = sensor_value_to_double(&die_temp);
		// print die temp
		#ifdef DEBUGGING
		printk("Die temperature: %f\n", die_temp_celsius);
		#endif

		//ENDOF: GET DIE TEMPERATURE

		// READ TEMPERATURE SENSORS
		for(int i = 0; i < NUMBER_OF_TEMP_SENSORS; i++){
			sensor_attr_set(temp_sensor_devices[i], SENSOR_CHAN_ALL,
				SENSOR_ATTR_W1_ROM, &rom_values[i]);
			ret = sensor_sample_fetch(temp_sensor_devices[i]);
			if (ret != 0) {
				#ifdef DEBUGGING
				printk("sample_fetch() failed for sensor %d: %d\n", i, ret);
				k_msleep(100);
				#endif
			}

			ret = sensor_channel_get(temp_sensor_devices[i], SENSOR_CHAN_AMBIENT_TEMP, &temp);
			if (ret != 0) {
				#ifdef DEBUGGING
				printk("channel_get() failed for sensor %d: %d\n", i, ret);
				k_msleep(100);
				#endif
			}

			tank_temperatures[i] = sensor_value_to_double(&temp);
			if(tank_temperatures[i] == 0){
				// wrong measurement. try again?
			}
			#ifdef DEBUGGING
			printk("Temp sensor %d: %f\n", i, tank_temperatures[i]);
			#endif
		}

		double tank_temperature_start = tank_temperatures[1];
		
		
		// ENDOF: READ TEMPERATURE SENSORS

		// dumbly just open the valves while we are above the voltage and temperature thresholds
		// temp threshold 50
		// voltage threshold 12.9
		//ret = pwm_set_dt(&pwm_dev, pwm_period_in_ns, pwm_period_in_ns); 
				k_msleep(500);
		while(/*battery_voltage_mv > 12400*/ die_temp_celsius < 50.0){
			#ifdef DEBUGGING
			//printk("Opening valve with modulation...\n");
			#endif
			//ret = pwm_set_dt(&pwm_dev, pwm_period_in_ns, pwm_period_in_ns*0.6); 

			// measure voltage and die temperature

			// GET DIE TEMPERATURE
			ret = sensor_sample_fetch(die_temp_sensor);
			if (ret != 0) {
				#ifdef DEBUGGING
				printk("sample_fetch() failed for die temp sensor: %d\n", ret);
				k_msleep(100);
				#endif
			}

			ret = sensor_channel_get(die_temp_sensor, SENSOR_CHAN_DIE_TEMP, &die_temp);
			if (ret != 0) {
				#ifdef DEBUGGING
				printk("channel_get() failed for die temp sensor: %d\n", ret);
				k_msleep(100);
				#endif
			}
			
			die_temp_celsius = sensor_value_to_double(&die_temp);
			// print die temp
			#ifdef DEBUGGING
			//printk("Die temperature: %f\n", die_temp_celsius);
			#endif

			// get the bottom and middle temperatures and print them
			for(int i = 0; i < NUMBER_OF_TEMP_SENSORS; i++){
				sensor_attr_set(temp_sensor_devices[i], SENSOR_CHAN_ALL,
					SENSOR_ATTR_W1_ROM, &rom_values[i]);
				ret = sensor_sample_fetch(temp_sensor_devices[i]);
				while (ret != 0) {
					#ifdef DEBUGGING
					//printk("sample_fetch() failed for sensor %d: %d\n", i, ret);
					k_msleep(100);
					#endif
					ret = sensor_sample_fetch(temp_sensor_devices[i]);
				}

				ret = sensor_channel_get(temp_sensor_devices[i], SENSOR_CHAN_AMBIENT_TEMP, &temp);
				if (ret != 0) {
					#ifdef DEBUGGING
					printk("channel_get() failed for sensor %d: %d\n", i, ret);
					k_msleep(100);
					#endif
				}

				tank_temperatures[i] = sensor_value_to_double(&temp);
				if(tank_temperatures[i] == 0){
					// wrong measurement. try again?
				}
				#ifdef DEBUGGING
				//printk("Temp sensor %d: %f\n", i, tank_temperatures[i]);
				#endif
			}
			printk("%f, %f, %f\n", tank_temperatures[0], tank_temperatures[1], tank_temperatures[2]);
			//k_msleep(1000);

		}		

		printk("Too hot or battery drained\n");
		printk("Battery voltage: %d mV, die temperature: %f C\n", battery_voltage_mv, die_temp_celsius);
		return 0;

		// CONTROL ALGORITHM

#if CONTROL_ALGORITHM == 1
		uint32_t control_loop_counter = 0; // to count how many times the valve has been opened 
		// control algorithm comes here.
		while(tank_temperatures[1] > tank_temperature_threshold && control_loop_counter < 5){ // this was 10 but then the motor drivers fried.
			// open valve until the temperature is no longer above threshold
			#ifdef DEBUGGING
			printk("Tank temperature: %f, threshold: %f \n", tank_temperatures[1], tank_temperature_threshold);
			#endif
			
			
			if(battery_voltage_mv > 13000 && die_temp_celsius < 50.0){
				// open valve for some time
				#ifdef DEBUGGING
				printk("Opening valve...\n");
				#endif
				ret = pwm_set_dt(&pwm_dev, pwm_period_in_ns, pwm_period_in_ns); 
				k_msleep(500);
				#ifdef DEBUGGING
				printk("Opening valve with modulation...\n");
				#endif
				ret = pwm_set_dt(&pwm_dev, pwm_period_in_ns, pwm_period_in_ns*0.6); 
				k_msleep(8500);
				#ifdef DEBUGGING
				printk("Closing valve...\n");
				#endif
				ret = pwm_set_dt(&pwm_dev, pwm_period_in_ns, 0); // turn off PWM
			} else {
				#ifdef DEBUGGING
				printk("Battery voltage too low to open valve: %u mV\n", battery_voltage_mv);
				#endif
				ret = pwm_set_dt(&pwm_dev, pwm_period_in_ns, 0); // turn off PWM
				break;
			}

			if (ret != 0) {
				#ifdef DEBUGGING
				printk("valve open failed: %d\n", ret);
				k_msleep(100);
				#endif
				return ret;
			}

			sensor_attr_set(temp_sensor_devices[1], SENSOR_CHAN_ALL,
				SENSOR_ATTR_W1_ROM, &rom_values[1]);
			ret = sensor_sample_fetch(temp_sensor_devices[1]);
			if (ret != 0) {
				#ifdef DEBUGGING
				printk("sample_fetch() failed for sensor %d: %d\n", 1, ret);
				k_msleep(100);
				#endif
			}

			ret = sensor_channel_get(temp_sensor_devices[1], SENSOR_CHAN_AMBIENT_TEMP, &temp);
			if (ret != 0) {
				#ifdef DEBUGGING
				printk("channel_get() failed for sensor %d: %d\n", 1, ret);
				k_msleep(100);
				#endif
			}

			tank_temperatures[1] = sensor_value_to_double(&temp);
			

			
			// measure battery voltage again
			(void)adc_sequence_init_dt(&adc_channels[0], &sequence);
			ret = adc_read_dt(&adc_channels[0], &sequence);
			if (ret < 0) {
				#ifdef DEBUGGING
				printk("Could not read (%d)\n", ret);
				#endif
			}

			val_mv = (int32_t)((int16_t)adc_measurement_buffer);
			ret = adc_raw_to_millivolts_dt(&adc_channels[0],&val_mv);

			if (ret < 0) {
				#ifdef DEBUGGING
				printk(" (value in mV not available)\n");
				#endif
			} else {
				float ratio = (12200.0f / 2200.0f); // voltage divider ratio
				battery_voltage_mv = (uint32_t)((float)val_mv * ratio);
				#ifdef DEBUGGING
				printk("Battery voltage reading: %d mV\n", battery_voltage_mv);
				#endif
			}


			
		

			control_loop_counter++; // to mark how many times the loop has run
			k_msleep(1000);
		}

		if(ret != 0){ // something is wrong if we reach here. Maybe the valves are not opening
			// we exited the control loop because we reached the maximum number of iterations
			// put an error code in the lora packet
			memset(lora_tx_buffer, 0xFF, 20); // the lora packet will be 20 bytes long in any case
		} else {
			// we exited the control loop normally, or never entered it

			uint32_t tank_temp_start_mcelsius = (uint32_t)(tank_temperature_start*1000);
			uint32_t tank_temp_end_mcelsius = (uint32_t)(tank_temperatures[1]*1000);
			uint32_t tank_temp_bottom_mcelsius = (uint32_t)(tank_temperatures[2]*1000);
			uint32_t tank_temp_top_mcelsius = (uint32_t)(tank_temperatures[0]*1000);
			uint32_t die_temp_mcelsius = (uint32_t)(die_temp_celsius*1000);

			// the data we will put in the lora packet consists of:
			// 4 bytes: battery voltage in mv
			// 4 bytes: tank temperature at the top in mC
			// 4 bytes: tank temperature at the middle in the beginning in mC
			// 4 bytes: tank temperature at the bottom in mC
			// // 4 bytes: number of times the valve was opened (uint32_t)
			// 4 bytes: tank temperature at the middle in the end in mC
			memcpy(&lora_tx_buffer[0], &battery_voltage_mv, 4);
			memcpy(&lora_tx_buffer[4], &tank_temp_top_mcelsius, 4);
			memcpy(&lora_tx_buffer[8], &tank_temp_start_mcelsius, 4);
			memcpy(&lora_tx_buffer[12], &tank_temp_bottom_mcelsius, 4);
			memcpy(&lora_tx_buffer[16], &tank_temp_end_mcelsius, 4);
			memcpy(&lora_tx_buffer[20], &die_temp_mcelsius, 4);
			//memcpy(&lora_tx_buffer[24], &tank_temp_bottom_mcelsius, 4);
			//memcpy(&lora_tx_buffer[28], &tank_temp_top_mcelsius, 4);

		}
		
		// LORA RADIO CONFIGURATION AND SEND PACKET
		// write lora config
		//gpio_pin_set_dt(&lora_en, 1);

		gpio_pin_set_dt(&lora_reset, 1);
		k_msleep(500);
		gpio_pin_set_dt(&lora_reset, 0);
		k_msleep(1500);

		gpio_pin_set_dt(&led_green, 1);

		ret = lora_config(lora_dev, &lora_configuration);
		if (ret < 0) {
			#ifdef DEBUGGING
			printk("LoRa configuration failed with error %d\n", ret);
			#endif
		}

		k_msleep(100);

		ret = lora_send(lora_dev, lora_tx_buffer, 24);
		if (ret == 0) {
		#ifdef DEBUGGING
			printk("LoRa send sucessful\n");
			k_msleep(100);
			#endif
		}
		if (ret < 0) {
			#ifdef DEBUGGING
			printk("LoRa send failed\n");
			k_msleep(100);
			#endif
		}

#endif


		// put to sleep
		#ifdef DEBUGGING
		printk("Entering sleep mode...\n");
		#endif
		// Enter deep sleep mode
		gpio_pin_set_dt(&led_green, 0);
		gpio_pin_set_dt(&led_red, 0);
		//gpio_pin_set_dt(&lora_en, 0);

		uint32_t current_ticks;
		counter_get_value(counter_dev, &current_ticks);

		counter_stop(counter_dev);
		
		k_msleep(1000*60*5 - current_ticks/10 - one_second_counter*1000); // sleep for 5 minutes
		//k_msleep(1000);
	}	

	return 0;
}
