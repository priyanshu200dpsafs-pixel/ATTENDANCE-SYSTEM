FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir \
    flask==2.3.3 \
    gunicorn==21.2.0 \
    numpy==1.24.3 \
    pandas==2.1.4 \
    opencv-python-headless==4.8.1.78 \
    deepface==0.0.79 \
    tensorflow-cpu==2.13.0 \
    tf-keras==2.13.0 \
    Pillow==10.1.0

COPY . .

RUN mkdir -p students

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
