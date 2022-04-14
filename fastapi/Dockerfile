FROM python:3.10.2

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
 
COPY app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9999"]
