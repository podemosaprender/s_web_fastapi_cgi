#S: web
#FROM: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#advanced-usage-with-scopes

from typing import Annotated, Optional, List
from typing_extensions import Doc
from datetime import timedelta
import json
import re

from util.logging import logm
from fastapi import Depends, Form, Body, Header, APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import NoResultFound
from util.db_cx_async import db_session
from util.fastapi import DbSessionT, RefererT, HostT, enc_uri

from .models import User, authenticate_user, update_scope, AuthScope, validate_scopes_for_token, token_for_claim_save, token_for_claim_load
from .token_no_db import Token, TokenData, TokenDataT, token_create, token_data, token_data_novalidate_user, HTTPExceptionUnauthorized
from .token import RequestUserT 

router= APIRouter(prefix="/auth")

@router.get("/login")
async def login_with_ui(
	host: HostT,	
	referer: RefererT= '',
	state: str= '', #SEE: https://www.oauth.com/oauth2-servers/server-side-apps/authorization-code/
	scope: str= '',
	code:  str= '',
	code_challenge: str= '', #SEE: https://www.oauth.com/oauth2-servers/pkce/authorization-code-exchange/
	code_challenge_method: str= '',
):
	login_tk= token_create(dict(
		code=code, state=state, scope=scope, referer= re.sub(r'[\?\#].*','',referer), #A: no search params or anchor
		code_challenge=code_challenge, code_challenge_method=code_challenge_method
	), timedelta(minutes=3)) #A: a temp token only for the login UI
	return RedirectResponse(f"http://{host}/static/login.html?tk={login_tk}")

@router.post("/token")
async def login_for_access_token(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	db_session: DbSessionT,
	extra: Annotated[Optional[str], Form()]= None,
	referer: RefererT= None,
	tk: Annotated[Optional[str], Form()]= None, #A: the them token only for the login UI
	redirect_uri: Annotated[Optional[str], Form()]= '',
) -> Token:
		
	user = await authenticate_user(form_data.username, form_data.password, db_session)
	if not user:
		raise HTTPExceptionUnauthorized

	scopes= form_data.scopes #U: space separated 
	(scopes_auth, scopes_not_validated)= await validate_scopes_for_token(user, scopes, db_session)
	
	extra_dict= {}
	if not extra is None and len(extra)>0:
		try:
			d= json.loads(extra)
			if type(d)==dict:
				extra_dict= d
			else:
				extra_dict['data']= d
		except:
			extra_dict['data']= extra

	extra_dict['scope']= extra_dict.get('scope',[])+ scopes_not_validated

	access_token = token_create( data={"sub": user.username,"scope": scopes_auth, "not_validated": extra_dict} )

	if form_data.grant_type=="password": #A: OAuth2 std
		return Token(access_token=access_token, token_type="bearer")
	else:
		tk_data= token_data_novalidate_user(tk) #A: MUST provide a temporary token generated by "/auth/login"
		if redirect_uri.startswith('http'):
			claim_id= await token_for_claim_save(
				db_session, access_token, 
				pkce_challenge= tk_data.get('code_challenge',''),
				pkce_method= tk_data.get('code_challenge_method','')
			)
			return RedirectResponse(
				url=f'{redirect_uri}?code={claim_id}&state={enc_uri(tk_data.get("state",""))}',
				status_code= status.HTTP_303_SEE_OTHER, #A: make browser GET the new url
			)

	raise HTTPExceptionUnauthorized() #DFLT

@router.post("/token/claim")
async def get_token_for_code_grant_type(
	db_session: DbSessionT,
	code: Annotated[str, Body(embed=True)],
	code_verifier: Annotated[Optional[str], Body(embed=True)]=None,
):
	try:
		tk= await token_for_claim_load(db_session, claim_id=code, pkce_verifier= code_verifier)
		return tk
	except Exception as ex:
		logm(m="TOKEN CLAIM",t="ERR", ex=ex, claim_id=code, pkce_verifier= code_verifier)
		pass #A: handled below

	raise HTTPExceptionUnauthorized() #DFLT

@router.get("/token/data/")
async def read_token_data(
	token_data: TokenDataT
) -> TokenData:
	return token_data

@router.get("/users/me/", response_model=User)
async def read_users_me(
	request_user: RequestUserT
):
	return request_user

#S: authorization {
@router.put("/scope/{scope_name:path}")
async def scope_edit_or_create(
	scope_name: str,	
	request_user: RequestUserT,
	db_session: DbSessionT,
	allow_all: Annotated[bool, Body(embed=True)]=False,
	users_add: Annotated[List[str], Body(embed=True)]=[],
	users_remove: Annotated[List[str], Body(embed=True)]=[],
) -> AuthScope:
	if not request_user: #XXX:genealize
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,)

	try:
		return await update_scope( request_user, scope_name, allow_all, db_session, users_add=users_add, users_remove=users_remove, wantsCreate=True)
	except Exception as ex:
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,)

#S: authorization }
