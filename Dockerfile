FROM python:3.8-alpine

WORKDIR /app

COPY req.txt .

RUN pip install -r req.txt

COPY . .

EXPOSE 6666

CMD ["python", "app.py"]