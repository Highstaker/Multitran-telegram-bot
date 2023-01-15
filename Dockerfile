FROM python:3.4

CMD ["mkdir","/multitran_bot"]
RUN ["apt", "update"]
RUN ["apt", "install", "-y", "virtualenv"]
RUN ["apt", "install", "-y", "python3-dev"]

COPY ["requirements.txt","/"]
RUN ["pip3", "install", "-r", "requirements.txt"]

WORKDIR /multitran_bot

ENTRYPOINT ["/bin/bash", "run_multitran_bot.sh"]

