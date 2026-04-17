FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py .
# This is the "Injected" file
COPY logic.py .
CMD ["python", "server.py"]