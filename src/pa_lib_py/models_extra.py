#INFO: agregados al ORM ej expresiones para queries
#VER: https://docs.djangoproject.com/en/3.0/howto/custom-lookups/

from django.db.models import Lookup
from django.db.models.fields import Field, DateTimeField
from django.conf import settings
from django.utils import timezone
from datetime import datetime

#S: funcs
def now():
	r= timezone.now() if settings.USE_TZ else datetime.now()
	return r

#S: operadores
@Field.register_lookup
class Like(Lookup):
	lookup_name = 'like'

	def as_sql(self, compiler, connection):
		lhs, lhs_params = self.process_lhs(compiler, connection)
		rhs, rhs_params = self.process_rhs(compiler, connection)
		params = lhs_params + rhs_params
		return '%s LIKE %s' % (lhs, rhs), params


#S: fields
class AutoUpdateDateTimeField(DateTimeField): #U: auto_now da warning de UTC en algunas versiones de django
	def pre_save(self, model_instance, add):
		t = now()
		setattr(model_instance, self.attname, t)
		return t

class AutoCreateDateTimeField(DateTimeField):
	def pre_save(self, model_instance, add):
		if not add:
			return getattr(model_instance, self.attname)
		t = now()
		setattr(model_instance, self.attname, t)
		return t
