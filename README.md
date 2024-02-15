# s_web_fastapi_cgi
FastApi + SQLModel + CGI

## Install deps with

~~~
python -mvenv xfastapi
. xfastapi/bin/activate
python requirements.py
~~~

On Windows use
~~~
python requirements.py
. xfastapi/Scripts/activate
~~~

## Run as standalone development server with

~~~
cd src
ENV=../env_devel.json uvicorn web_main:app --reload
~~~

run `test/simple.sh` or

* go to http://127.0.0.1:8000/docs
* go to POST, "Try it out", edit de json file to add some heroes
* go to GET and see your list

## Run as cgi with

XXX:update to new std_env scripts

(edit variables inside this script as needed)

## Source code 

under `src/`

* Specific for this app
   * form_app: we create a dir for each "app" (like django), NOTICE models my be used separatedly e.g. by discord bots, scripts, etc.
   * static: any static files we may deploy to a faster, optimized static web server
* Generic for many apps
   * web_main
   * util

You shouldn't change the code generic for many apps BUT in case you make a *generic* improvement please notify everybody.

## Other database examples

SEE: https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-hero-api/

## Auth JWT

Create / update users
~~~
(cd src; python -m auth_app.cmd user-update --password secreto xuser1)
~~~

1. Get token with xuser1 / secreto in http://127.0.0.1:8000/docs#/default/login_for_access_token_auth_token_post
2. copy the token with quotes 
3. on the terminal write `token=` and paste the token with quotes
4. on the terminal paste `curl -H "Authorization: Bearer $token" http://localhost:8000/auth/users/me/`

to set the variable automatically
~~~
token=`curl -X 'POST' 'http://localhost:8000/auth/token' -H 'accept: application/json' -H 'Content-Type: application/x-www-form-urlencoded'  -d 'grant_type=password&username=xuser1&password=secreto&scope=&client_id=&client_secret=' | cut '-d"' -f4 ` ; echo $token
~~~

Check it
~~~
curl -X GET -H "Authorization: Bearer $token" -H 'Content-type: application/json'  "http://localhost:8000/auth/token/data/"
~~~

To create an AuthScope:

~~~
curl -X PUT -H "Authorization: Bearer $token" -H 'Content-type: application/json'  -d '{"allow_all": false}' "http://localhost:8000/auth/scope/@xuser1/llamada"
~~~

add or remove users, idempotent, may be created in the same operation
~~~
curl -X PUT -H "Authorization: Bearer $token" -H 'Content-type: application/json'  -d '{"allow_all": false, "users_add": ["ana","mariana","jose"], "users_remove": ["pepe","maria"]}' "http://localhost:8000/auth/scope/@xuser1/llamada3"
~~~

### Generate token with scopes and extra data

~~~
token=`curl -X 'POST' 'http://localhost:8000/auth/token' -H 'accept: application/json' -H 'Content-Type: application/x-www-form-urlencoded'  -d 'grant_type=password&username=xuser1&password=secreto&scope=@xuser2/b2+scp2&client_id=&client_secret=&extra={"hola": "mau"}' | cut '-d"' -f4 ` ; echo $token | wc -c
~~~

check what's included in your jwt / available to the receiving application. **NOTICE** there is a `not_auth` key for everything the API can't validate, and **must be treated ONLY as user entered info**

~~~
curl -X GET -H "Authorization: Bearer $token" -H 'Content-type: application/json'  "http://localhost:8000/auth/token/data/"
{"username":"xuser1","scopes":["@xuser2/b2"],"payload":{"sub":"xuser1","scope":["@xuser2/b2"],"not_auth":{"hola":"mau","scope":["scp2"]},"exp":1707919268}}
~~~

### Generate your keys

~~~
KEY=devel
openssl genrsa -out ${KEY}_key_private.pem 4096
openssl rsa -in ${KEY}_key_private.pem -pubout -out ${KEY}_key_public.pem
~~~

## SEE ALSO:

https://www.starlette.io/routing/#path-parameters
