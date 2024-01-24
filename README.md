# s_web_fastapi_cgi
FastApi + SQLModel + CGI

## install deps with

~~~
python -mvenv xfastapi
. xfastapi/bin/activate
pip install -r requirements.txt
~~~

On Windows use
~~~
. xfastapi/Scripts/activate
~~~

## run as standalone server with

~~~
cd src
uvicorn app_simple:app --reload
~~~

run `test/simple.sh` or

* go to http://127.0.0.1:8000/docs
* go to POST, "Try it out", edit de json file to add some heroes
* go to GET and see your list



## run as cgi with

~~~
cd test
./cgi.sh
~~~

(edit variables inside this script as needed)

## Try other database examples
SEE: https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-hero-api/

