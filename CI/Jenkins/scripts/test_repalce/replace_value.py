import os 
import sys
import subprocess
import yaml
DEPLOY_PATH = '/gpfs/fuyun'
# FY_MODULENAME = 'genray/201213-gompi-2019b'
def replace_value(modulename,tmpname):
    os.environ['Modulename'] = str(modulename)
    # os.environ['Modulename_version'] = str(FY_MODULEVERSION)
    os.system('(module spider $Modulename) 2>/tmp/$Modulename_version.log') 
    #os.system('cmd1 && cmd2') get the direcotry of successful eb file ,and the best way is copy it to the key [build]
    cmd1 = "module use "+ DEPLOY_PATH+ "/modules/all"
    cmd2 = " module load "+ modulename
    cmd3 = "echo $EBROOTGENRAY"
    cmd = cmd1 + " && " + cmd2 + " && "+ cmd3
    print(cmd)
    out=subprocess.run(cmd,stdout=subprocess.PIPE,shell=True).stdout.decode('utf-8').replace('\n', '').replace('\r', '')
    # result3 = subprocess.run(cmd, stdout=subprocess.PIPE)
    # module use /gpfs/fuyun/modules/all &&  module load genray/201213-gompi-2019b && echo $EBROOTGENRAY'
    print(out)
    
    filename = os.path.join(os.path.dirname(__file__),tmpname).replace("\\","/")
    f = open(filename)
    y = yaml.load(f)
    print(filename)
    with open(tmpname) as f:
        print(tmpname)
        doc = yaml.load(f)
        print(doc)
        print(out)       
        doc['build']['eb'] = out
    with open(tmpname, 'w',encoding='utf-8') as f:
        yaml.safe_dump(doc, f, default_flow_style=False,encoding='utf-8',allow_unicode=True)
if __name__=='__main__':
    replace_value(sys.argv[1],sys.argv[2])
    # falg_value=check_filename_exit(sys.argv[1],sys.argv[2])
    # if(falg_value=0):
    #     tmpl_falg_value=check_filename_exit(sys.argv[1],sys.argv[3])
    #     if(tmpl_falg_value=1):
    #         cp sys.argv[3] sys.argv[4]+"/"+sys.argv[1]

    # # print(len(falg_value))
    # print(falg_value)
