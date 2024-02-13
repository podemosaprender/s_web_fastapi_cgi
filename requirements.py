#INFO: install latest version main packages, stay up to date, freeze only for deployment

import sys
import os

PACKAGES=[
  'click', #U: command line parameters
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
	'bcrypt==4.0.1', #U: backend for passlib, this older version required
]

if not '-nopg' in sys.argv:
	PACKAGES= PACKAGES+ ['asyncpg']

os.system('pip install --upgrade pip')
for pkg in PACKAGES:
	os.system(f"pip install {pkg}")
