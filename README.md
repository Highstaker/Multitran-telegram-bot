# Multitran-telegram-bot
A translator bot that uses Multitran online dictionary.

##Overview

##Deployment

Make sure **Python 3** and **virtualenv** are installed.

First, run `sudo apt-get install libfreetype6-dev libpng12-dev`

I also needed to do `ln -s /usr/include/freetype2/ft2build.h /usr/include/` because certain libraries did not compile without that.

Then, run _setup.sh_. This will install dependencies.

To run the bot, simply run _run.sh_.

###Deploying with webhooks and `nginx`

Install *nginx* using `apt-get install nginx`
Go to `/etc/nginx/sites-enabled` and create new file with the following contents.
```
server {
    listen              443 ssl;
    server_name         111.111.111.111; #IP address of your server
    ssl_certificate     /somepath/certs/cert.pem; #path to your ssl certificate file
    ssl_certificate_key /somepath/certs/private.key; #path to your ssl private key file


location /BOT_TOKEN {
    proxy_pass http://127.0.0.1:33333; #port is arbitrary, the one you set upon launching the bot
        }
}

```

Go to `/etc/nginx/sites-enabled` and delete the default <s>cube</s> link.
Create a link to your settings file. `ln -s /etc/nginx/sites-enabled/your_config /etc/nginx/sites-enabled`

Perform `nginx -s reload` to reload the configuration.

Modify your _run.sh_ so it would be something like this, replacing the values with your values, of course.
`env/picbot_env/bin/python3 multitran_bot.py --server-ip="111.111.111.111" -m "webhook_nginx" -p 33333 -c "/somepath/certs/cert.pem"`


##Dependencies

This program uses **Python 3**

This program relies on [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).

##Tested systems

Ubuntu 14.04
