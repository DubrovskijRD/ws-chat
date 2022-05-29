from python:3.8

copy . /app
workdir /app

run pip install -r requirements.txt

cmd ["gunicorn", "src.application.app:app_factory", "-b", ":8080", "--worker-class", "aiohttp.GunicornWebWorker"]