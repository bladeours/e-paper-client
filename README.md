# e-paper client
App for Raspberry Pico that let you get image from [e-paper server](https://github.com/bladeours/e-paper-server) and display it.

## Table of Contents
* [General Info](#general-info)
* [Example](#example)
* [Technologies Used](#technologies-used)
* [Setup](#setup)
* [Config](#config)

## General Info
I've created this app for my project that uses Raspberry pico and [Waveshare e-ink screen](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_(B)_Manual).
It allows me to display calendar (or any other image actually) from [e-paper server](https://github.com/bladeours/e-paper-server)
and I can have an e-ink display in photo frame from IKEA that shows me all of my events.

## Example
![sample view](eink-sample.jpg)

## Technologies Used
* micropython
* Raspberry Pico
* [7.5 inch e-ink display](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_(B)_Manual#Introduction)
* drivers from Waveshare website

## Setup
Here is [documentation](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_(B)) how to work with micropython.

## Config
This app needs `.config` file:
```
ssid=<wifi-ssid>
password=<wifi-password>
url=<url-to-get-image>
refresh_period_min=60
max_retries_download_calendar=10
delay_retry_download_calendar_s=5
timeout_download_calendar_s=14

max_retries_download_calendar=10
timeout_connect_wifi_s=15
```