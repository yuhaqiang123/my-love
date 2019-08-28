import time
import os
filePath = './'
for i,j,k in os.walk(filePath):
    for f in k:
    	if ".xmind" in f:
    		f_name="%s/%s"%  (i, f)
    		f_name=f_name.replace(" ","\\ ")
    		f_name=f_name.replace("&", "\\&")
    		shell_cmd = "xmindparser %s -json" % f_name
    		os.system(shell_cmd)
