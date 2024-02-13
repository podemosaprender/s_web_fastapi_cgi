#INFO: command line control of the auth_app

import click
import asyncio

from util.cfg import cfg_init
cfg_init() #A: other modules may depend
from util.db_cx_async import db_init, session_async
from sqlalchemy.exc import NoResultFound

from .models import update_user

@click.group()
def cli():
	pass	

@cli.command() 
@click.option('--create/--no-create', default=False)
@click.option('--email', default=None)
@click.option('--fullname', default=None)
@click.option('--password',default=None)
@click.argument('username', type=str)
def user_update(create, email, fullname, password, username):
	kv= {}
	if email: kv['email']=email
	if fullname: kv['full_name']=fullname

	async def async_impl():
		await db_init()
		async with session_async() as cx:
			try:
				u= await update_user(username, kv, password, create, cx)
				print(f"OK {u.model_dump()}")	
			except NoResultFound as ex:
				print(f"user does not exist {username}")
	
	asyncio.run(async_impl())	

if __name__=="__main__":
	cli()	
