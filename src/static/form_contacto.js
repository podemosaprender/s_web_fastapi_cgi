//INFO: contact form script to include in any html

const DBG= window.DBG_FORM; //U: set DBG_FORM=true before loading this script to enable debugging

const URL= 'http://localhost:8000/contacto_form/' //U: where to post //XXX:ajustar al host publico!
const FORM_SELECTORS=['.php-email-form'] //U: how to find the forms //XXX:que pueda cambiar como DBG

DBG && console.log("FORM", {URL, FORM_SELECTORS});

function feedback(form_el, show) {
	const feedback_els= {
		error: form_el.querySelector('.error-message'),
		ok: form_el.querySelector('.sent-message'),
		loading: form_el.querySelector('.loading'),
	}
	Object.entries(feedback_els).forEach( 
		kv => { kv[1].style.display= kv[0]==show ? 'block' : 'none'}
	);
}

async function onSubmitImpl(e) {
	DBG && console.log('FORM onSubmit', e);
	const form_el= e.target;

	feedback(form_el, 'loading')
	const data= new FormData(form_el)
	data.append('dontRedirect', true)

	let res= ''
	try {
		res= await fetch(URL, { method: 'POST', body: data} ).then( xres => xres.text() )
		DBG && console.log('FORM SENT', res);
	} catch (ex) {
		DBG && console.log('FORM ERROR', ex);
	}
	feedback(form_el, res=='ok' ? 'ok' : 'error')
	return false;
}

function onSubmit(e) { e.preventDefault(); onSubmitImpl(e); return false; }

FORM_SELECTORS.forEach(selector => 
	document.querySelectorAll(selector).forEach(el => {
		el.addEventListener('submit', onSubmit)
		feedback(el) //A:Hide all messages
		DBG && console.log("FORM EL FOUND", el);
	})
)

