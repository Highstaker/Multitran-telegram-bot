#!/bin/bash

cd `dirname $0`

mkdir tokens
touch tokens/token

mkdir env
#create environment
virtualenv env/picbot_env
# install dependencies
env/picbot_env/bin/python3 env/picbot_env/bin/pip3 install -r requirements.txt

RUN_SCRIPT_NAME=run_multitran_bot.sh

echo "#!/bin/bash

env/picbot_env/bin/python3 multitran_bot.py

exit 0
" > $RUN_SCRIPT_NAME

chmod +x $RUN_SCRIPT_NAME

exit 0