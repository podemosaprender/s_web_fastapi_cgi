#!/bin/sh

curl -X 'POST' \
  'http://127.0.0.1:8000/heroes/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 1,
  "name": "messi",
  "secret_name": "GOAT",
  "age": 30
}'

curl -X 'POST' \
  'http://127.0.0.1:8000/heroes/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "name": "Maradona",
  "secret_name": "D10s",
  "age": 60
}'

curl -X 'GET' \
  'http://127.0.0.1:8000/heroes/' \
  -H 'accept: application/json'
