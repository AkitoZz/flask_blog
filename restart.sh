#!/bin/bash

ps -ef |grep python |grep manager.py |grep 8080 |grep -v grep |awk '{print $2}' | xargs  kill -9

nohup /root/anaconda3/envs/venv_py37/bin/python manager.py runserver -h 0.0.0.0 -p 8080 & >> log/nohup.out

