#INFO: install latest version main packages, stay up to date, freeze only for deployment

import sys
import os

PACKAGES=[
	'fastapi',
	'sqlmodel',
	'pydantic',
	'annotated-types',
	'email-validator',
	'python-multipart',
	'a2wsgi', #U: cgi adapter
	'uvicorn', #U: asgi runner
	'SQLAlchemy',
	'aiosqlite', #U: we always include sqlite for testing, etc
	'"python-jose[cryptography]"', #U: for JWT Auth
	'passlib', #U: hash pass
]

if not '-nopg' in sys.argv:
	PACKAGES= PACKAGES+ ['asyncpg']

os.system('pip install --upgrade pip')
for pkg in PACKAGES:
	os.system(f"pip install {pkg}")
