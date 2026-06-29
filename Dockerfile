FROM python:3.11

RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

COPY . .

RUN pip install pandas sqlalchemy pyodbc requests

CMD ["python", "main.py"]