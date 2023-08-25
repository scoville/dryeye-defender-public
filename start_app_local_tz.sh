#!/bin/bash

# Read the timezone from a file on the host
HOST_TIMEZONE=$(cat /etc/timezone)

# Start the Docker service using docker-compose with the dynamically set timezone
TZ=$HOST_TIMEZONE docker-compose up 
