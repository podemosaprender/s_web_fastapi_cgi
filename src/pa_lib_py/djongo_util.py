import re
import json
from .logging import logm, onLogLvlMaxChange, willLog

HAS_MONGO= False #DFLT
try:
	from pymongo import monitoring
	HAS_MONGO= True

	#VER: https://docs.mongoengine.org/guide/logging-monitoring.html
	class CommandLogger(monitoring.CommandListener):
		def started(self, event):
			def fmt(x):
				return (f"XXX_ISODate_XXX{x.isoformat()}" if hasattr(x,'isoformat') else str(x))

			def toString():
				cmd= event.command.to_dict() if hasattr(event.command,'to_dict') else event.command
				if cmd.get('aggregate'):
					x= re.sub(r'"XXX_ISODate_XXX([^"]+)"','ISODate("\\1")',json.dumps(cmd.get("pipeline"), default=fmt))
					s= f"\n	db.{cmd.get('aggregate')}.aggregate({x})\n"
				else:
					s= re.sub(r'"XXX_ISODate_XXX([^"]+)"','ISODate("\\1")',json.dumps(cmd, default=fmt))
				return s

			logm(ch="mongo", l=7, m="mongo", event=event, cmd=toString)

		def succeeded(self, event):
			logm(ch="mongo", l=9, m="mongo", event=event)

		def failed(self, event):
			logm(t="ERR", ch="mongo", l=8, m="mongo", event=event)

	def checkIfNeeded():
		logm("checkIfNeeded {HAS_MONGO}")
		if HAS_MONGO and willLog(3, "mongo"):
			monitoring.register(CommandLogger())

	onLogLvlMaxChange(checkIfNeeded)

except:
	pass



