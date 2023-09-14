FROM python:3.11-alpine

WORKDIR .

RUN apk add --no-cache gcc musl-dev linux-headers geos libc-dev postgresql-dev build-base
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 5002

COPY . .
CMD ["flask", "run", "--host", "0.0.0.0"]