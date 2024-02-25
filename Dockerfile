FROM python:3.11

WORKDIR /app
COPY . /app

RUN apt-get -y update
RUN apt-get install --no-install-recommends -y ffmpeg

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

#CMD ["python3", "src/main.py"]
