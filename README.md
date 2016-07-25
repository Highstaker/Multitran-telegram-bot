# Multitran-telegram-bot
A translator bot that uses Multitran online dictionary.

##Overview

##Deployment

Make sure **Python 3** and **virtualenv** are installed.

First, run `sudo apt-get install libfreetype6-dev libpng12-dev`

I also needed to do `ln -s /usr/include/freetype2/ft2build.h /usr/include/` because certain libraries did not compile without that.

Then, run _setup.sh_. This will install dependencies.

To run the bot, simply run _run.sh_.

##Dependencies

This program uses **Python 3**

This program relies on [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).

##Tested systems

Ubuntu 14.04
