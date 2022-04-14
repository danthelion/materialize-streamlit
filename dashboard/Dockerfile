FROM python:3.10.2

ENV DOCKERIZED true

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py main.py

CMD ["streamlit", "run", "main.py"]
