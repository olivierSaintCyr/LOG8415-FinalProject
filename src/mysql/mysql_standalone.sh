#!/bin/bash

# Update and install packages
sudo NEEDRESTART_MODE=a apt-get update -y
sudo NEEDRESTART_MODE=a apt-get install git -y
sudo NEEDRESTART_MODE=a apt-get install python3-pip -y

sudo NEEDRESTART_MODE=a apt-get install mysql-server -y
