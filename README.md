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

1. Get token with johndoe / secreto in http://127.0.0.1:8000/docs#/default/login_for_access_token_auth_token_post
2. copy the token with quotes 
3. on the terminal write `token=` and paste the token with quotes
4. on the terminal paste `curl -H "Authorization: Bearer $token" http://localhost:8000/auth/users/me/`


sqlite> insert into user (username, hashed_password) values('johndoe','$2b$12$WVU7gQ2RqBp7I9BQB1e5gO06MnRstY3ybUyWhH/iVv4zd9zPRh3KG');
