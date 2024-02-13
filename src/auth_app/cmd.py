#INFO: command line control of the auth_app

import click
import asyncio

from util.logging import logm
from util.cfg import cfg_init, cfg_for
cfg_init() #A: other modules may depend
from util.db_cx_async import db_init, session_async

from .models import User, set_user_password

@click.group()
def cli():
	pass	

@cli.command() 
@click.argument('username', type=str)
@click.argument('password',type=str)
def user_add(username, password):
	async def async_impl():
		await db_init()
		async with session_async() as cx:
			u= User(username=username)
			await set_user_password(u, password, True, cx)
			print("OK")	
	
	asyncio.run(async_impl())	

if __name__=="__main__":
	cli()	
