import code 

def debug(vglobals, vlocals): #U: debug(globals(),locals())
	variables = vglobals.copy() 
	variables.update(vlocals) 
	shell = code.InteractiveConsole(variables) 
	shell.interact() 


