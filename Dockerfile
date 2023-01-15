FROM python:3.4

CMD ["mkdir","/multitran_bot"]
RUN ["apt-get", "update"]
RUN ["apt-get", "install", "-y", "python3-dev"]

COPY ["requirements.txt","/"]
RUN ["pip3", "install", "--default-timeout=100", "-r", "requirements.txt"]

WORKDIR /multitran_bot

ENTRYPOINT ["/bin/bash", "run_multitran_bot.sh"]
