#!/bin/bash

pip list --format=freeze > requirements.txt

echo "requirements.txt 파일이 생성되었습니다."