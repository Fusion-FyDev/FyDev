# from FyDev.python.tests.test_basic import module
# from FyBuild.python.fypm.writefile import generate_yaml_doc_ruamel
import collections
import os
import sys
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
import pathlib
import shlex
import subprocess
import signal
import traceback
import uuid
import re
from pathlib import Path, PurePath,PurePosixPath
import time
import linecache
import yaml

from spdm.util.logger import logger

from .trash.FyHandler import FyModule
from .StandardModule import  StandardModule
import .EasyBuildPa as bs



class ModulePa(FyModule):
    '''Module wrapper.

    This class represents internally a module. Concrete module system
    implementation should deal only with that.
    the init will provide the name ,version ,tag and fullname .
    if the version is null ,I dont know what you want .
    If the tag is null ,I can read the default tag from configure,yaml \
        which by def load_configure() in class ModuleRepository .
    '''

    def __init__(self, name, version,tag,collection=False, path=None,repo_name=None, repo_tag=None,*args,**kwargs):

        super().__init__(repo_name=None, repo_tag=None,*args ,**kwargs)
        
        name = name.strip()
        if not name:
            raise ValueError('module name cannot be empty,I dont know what you want')
        if not isinstance(name, str):
            raise TypeError('module name not a string')

        version = version.strip()

        if not isinstance(version, str):
            raise TypeError('module version not a string')

        tag = tag.strip()  
        if not isinstance(tag, str):
            raise TypeError('module tag not a string')            

        # first check the contition ,get the all value
        if not version:
        # for version=NULL , if need to give the error and exit????
            try:
                logger.warning(f"the version is empity,I dont know what you want "
                                f"you can use fetch to check which module is installed")
                self._name = name
                self._version = " "
                self._tag = " "
                self._fullname = name
            except:
                raise ValueError(f"the version is empity,I dont know what you want ")
        elif tag :
            try :
                self._name = name
                self._version = version
                self._tag = tag
                self._modulename = '-'.join((self._name, self._version))
                self._fullname = '-'.join(('/'.join((self._name, self._version)),self._tag))
            
            except :
                raise ValueError('I cannot get fullname ,I dont know what you want')            
        else :
            try:
                """
                default_tag = self.load_configure(self),here is the interface with the class ModuleRepository
                which get the default tag from the configure file .
                """
                # default_module = self.__init__( name, version,tag,collection=False, path=None,repo_name=None, repo_tag=None,*args,**kwargs)
                # path="/scratch/liuxj/FYDEV-Workspace/FyDev/python/tests/data/FuYun/configure.yaml"
                self.load_configure(path)
                default_tag = self._conf.get("default_toolchain")
                logger.debug(f"the default_tag name from the default-configure  is '{default_tag}'")
                # default_tag = 'foss-2020a'
                self._name = name
                self._version = version
                self._tag = default_tag
                self._modulename = '-'.join((self._name, self._version))
                self._fullname = '-'.join(('/'.join((self._name, self._version)),self._tag))
                # self.eb_options = eb_options
            except :
                raise ValueError('I cannot get name ,I dont know what you want')            
                
        self._path = path
        self._ebfilename = '-'.join(self._fullname.split('/'))



    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def tag(self):
        return self._tag

    @property
    def path(self):
        return self._path

    @property
    def modulename(self):
        return self._modulename

    @property
    def fullname(self):
        return self._fullname

    @property
    def ebfilename(self):
        return self._ebfilename

  

    def __hash__(self):
        # Here we hash only over the name of the module, because foo/1.2 and
        # simply foo compare equal. In case of hash conflicts (e.g., foo/1.2
        # and foo/1.3), the equality operator will resolve it.
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        if self.path != other.path:
            return False

        if not self.version or not other.version:
            return self.name == other.name
        else:
            return self.name == other.name and self.version == other.version

    def __repr__(self):
        return self.fullname

    def __str__(self):
        return self.fullname
    

    
    def execute(self, cmd, *args):
        '''Execute an arbitrary module command using the modules backend.

        :arg cmd: The command to execute, e.g., ``load``, ``restore`` etc.
        :arg args: The arguments to pass to the command.
        :returns: The command output.
        '''
        try:
            exec_output = self._execute_modulecmd(cmd, *args)
        except :
            raise RuntimeError('could not execute module operation') 

        return exec_output

    def modulecmd(self, *args):
        lmod_cmd = os.getenv('LMOD_CMD')
        if lmod_cmd is None:
            raise RuntimeError('could not find a sane Lmod installation: '
                              'environment variable LMOD_CMD is not defined')

        return ' '.join([lmod_cmd, 'python', *args])

    def _run_command(self,cmd, check=False, timeout=None, shell=False, log=True):
        # logger.debug(f"CMD: {cmd} : {res}")
        logger.info(f"Execute Shell command {cmd}")
        # @ref: https://stackoverflow.com/questions/21953835/run-subprocess-and-print-output-to-logging
        # if isinstance(cmd, str) and not shell:
        #     cmd = shlex.split(cmd)
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                encoding="utf-8"
            )
            
            # with process.stdout as pipe:
            #     for line in iter(pipe.readline, b''):  # b'\n'-separated lines
            #         logger.info(line)
            # process = subprocess.Popen(cmd,
            #                 stdout=subprocess.PIPE,
            #                 stderr=subprocess.PIPE,
            #                 stdin=subprocess.DEVNULL,
            #                 universal_newlines=True,
            #                 shell=shell)
            proc_stdout, proc_stderr = process.communicate(timeout= None)
            
            # for line in proc_stdout :  # b'\n'-separated lines
            #     logger.info(line)
            # logger.info(f"Execute the proc_stdout is {proc_stdout}")
            # logger.info(f"Execute the proc_stderr is {proc_stderr}")
        except subprocess.TimeoutExpired as e:
            os.killpg(process.pid, signal.SIGKILL)
            raise RuntimeError(e.cmd,
                                        process.stdout.read(),
                                        process.stderr.read(), timeout) from None            
            # process_output, _ = command_line_process.communicate()
        completed = subprocess.CompletedProcess(cmd,
                                                returncode=process.returncode,
                                                stdout=proc_stdout,
                                                stderr=proc_stderr)
        if check and process.returncode != 0:
            raise process.subprocessCalledProcessError(completed.args,
                                  completed.stdout, completed.stderr,
                                  completed.returncode)



        #     exitcode = process.wait()

        # except (OSError, subprocess.CalledProcessError) as error:
        #     logger.error(
        #         f"""Command failed! [{cmd}]
        #            STDOUT:[{error.stdout}]
        #            STDERR:[{error.stderr}]""")
        #     raise error
        return completed

    def _execute_modulecmd(self, cmd, *args):
        # get the command ,such as : /usr/share/lmod/lmod/libexec/lmod  -t avail 'substr'
        modulecmd = self.modulecmd(cmd, *args)
        # modulecmd = "/usr/share/lmod/lmod/libexec/lmod purge " + "&&" + ' ' + modulecmd
        print("the module cmd is",modulecmd)

        completed = self._run_command(modulecmd)
        namespace = {}
        exec(completed.stdout,{},namespace)

        # if completed.stderr == '':
        #     return namespace.get('_ml_status')
        # else :
        #     return completed.stderr
        if not namespace.get('_ml_status', True):
            return namespace.get('_ml_status')
        elif completed.stderr == '' :
            return namespace.get('_ml_status')
        else:
            return completed.stderr

        # print("the result completed is :",completed)
        
        # print("the stdout of completed is ",completed.stdout)
        # print("the stderr of completed is ",completed.stderr)
        # if re.search(r'\bERROR\b', completed.stderr) is not None:
        #     print("I believe this is null")
        #     raise subprocess.CalledProcessError(modulecmd,
        #                               completed.stdout,
        #                               completed.stderr,
        #                               completed.returncode)

        # exec(completed.stdout)
       
       
    def init_package(self, *args,**kwargs):
        """
         init the package ,and to check name ,version ,toolchain-tag 
        Args:
            spec ([type]): [description]
        """
        """
            to test print the vars in module class
        """
        logger.debug(f"the package name is '{self.fullname}'")
        #return result is class
        return self.fullname
    
    def list_package(self, *args,max_list ,**kwargs):
        # to list the related modulename which is installed 

        fullname = self.init_package(*args,**kwargs)
        if max_list == True:
            fullname = self.name
        logger.info(f"the packages name is {fullname}")
        output = self.execute('-t', 'avail', fullname)  
        ret = []
        for line in output.split('\n'):
            if not line or line[-1] == ':':
                # Ignore empty lines and path entries
                continue
            module = re.sub(r'\(\S+\)', '', line)
            logger.info(f"the module is {module}")
            ## what's different between the flowing two lines???
            # ret.append(StandardModule(module))
            ret.append(module)
        return [str(m) for m in ret]


    def check_package(self,*args,**kwargs):
        # to check the modulename which will be install is installed or not 
        fullname = self.init_package(*args,**kwargs)
        if not isinstance(fullname, str):
            raise TypeError('module name not a string')
        if fullname.find("/") != -1:
            try:
                print(f"module purge && module load {fullname}")
                # self.execute('purge')
                #we need to run purge and then module load 
                output = self.execute('load',fullname)
                logger.debug(f"the output is {output}")
                return output
            except output == 'None'   :
                logger.debug(f"The package {fullname} is not install in this system , \
                and I list all other version in this system ; \
                and you can refer it to choose which one is best for you ,or you install the {fullname} ")
                self.list_package(fullname,max_list = True)

    def fetch_max(self, **kwargs):
        #because is max ,so just work for name  
        substr = self.init(**kwargs)
        # substr = self._fullname
        output = self.execute('-t', 'avail', substr)
        # the output is standard moudles ,such as genrar/2013-foss-2021a
        # print("the out put is",output)
        ret = []
        for line in output.split('\n'):
            if not line or line[-1] == ':':
                # Ignore empty lines and path entries
                continue
            # print(line)
            module = re.sub(r'\(\S+\)', '', line)
            print("the module is",module)
            ## what's different between the flowing two lines???
            # ret.append(StandardModule(module))
            ret.append(module)
        return [str(m) for m in ret]
        # return ret 

    def fetch_min(self, **kwargs):
        """
        because is min ,so just work for name/version-tag ,so now we need to check the version 
        and tag .if version and tag is null ,we need read the basic information from the configure.yaml.
        such as :  
        version is null ,then I cannot work ,I dont know what you want ,and I just fetch the max to you.
        version is not null:
            tag is null ,and tag = default-tag ,then fetch_min(name/version-default-tag )
            tag is tag ,then fetch_min(name/version-tag)
        """
        substr = self.init(**kwargs).fullname
        logger.info(f"the init result  is {substr}")
        output = self.execute('-t', 'avail', substr)
        # print("the out put is",output)
        ret = []
        for line in output.split('\n'):
            if not line or line[-1] == ':':
                # Ignore empty lines and path entries
                continue
            print(line)
            module = re.sub(r'\(\S+\)', '', line)
            print("the module is",module)
            ret.append(StandardModule(module))
            # ret.append(module)
        return [str(m) for m in ret]
        # return ret


    def list_dependence(self,*args,**kwargs):
        logger.debug("the install is finish ,you can use it by module load modulename \
                if the check_package(new package) is fail ,to prove the install is fall ")  
        fullname = self.init_package(*args,**kwargs)
        path=self.path
        listdependflag = 0
        dependlist=[]
        if self.check_package(fullname) == False:
            self.load_configure(path)
            # if self.check_package(fullname) == False:
            environ = 'GCC'
            build_system = bs.EasyBuild()
            # easyconfigs = ['Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb']
            easyconfigs = [self._ebfilename+'.eb']
            build_system.easyconfigs = easyconfigs
            # options= ['-Dr',"--minimal-toolchains","--try-update-deps","--experimental"]
            list_cmd = self._conf.get("list_cmd")
            eb_options = self._conf.get("eb_options")

            logger.debug(f"the eb options is {eb_options} ")
            logger.debug(f"the eb options is {list_cmd} and the type is {type(list_cmd)} ")
            eb_options.insert(0,list_cmd)
            logger.debug(f"the options is {eb_options} ")
            build_system.options =  eb_options
            # build_command.prefix = self.install_dir
            build_system.prefix = '/gpfs/fuyun'
            build_command = build_system.emit_build_commands("GCC")
            # build_command = 'eb Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb -Dr --minimal-toolchains --try-update-deps --experimental'
            build_system_out = self._run_command(build_command)
            
            # logger.debug(f' the type is {type(build_system_out.stdout)} and  the line is {len(build_system_out.stdout)}')
            allout1=build_system_out.stdout.split("\n")
            
            for i,val in enumerate(allout1):
                logger.debug(f'the num is {i} and the value is {val}')
                if val.find("Dry run: printing build status of easyconfigs and dependencies") >=0:
                    listdependflag+=1
            # logger.debug(f'the value is {listdependflag}')
            if listdependflag == 1:
                # logger.debug(f'the value is {listdependflag}')
                for i in range(len(allout1)):
                    # logger.debug(f'the value is {allout1[i]}')
                    # logger.debug(f'the startswith is {allout1[i].lstrip().startswith("*")}')
                    # logger.debug(f'the findall is {re.findall(r'module:',allout1[i])}')
                    if allout1[i].lstrip().startswith("*") and  re.findall(r'module:',allout1[i]) :
                        # logger.debug(f'the module value is {allout1[i]}')
                        dependlist.append(allout1[i].split(" ")[-1][:-1])
                        # logger.debug(f'the value is {listdependflag}')
                logger.debug(f'the depend list  is {dependlist}')
                return build_command, dependlist
            else:
                raise ValueError('the check ebfile is fail,please check them again!')
                sys.exit(1)        
        else:
            moduleinstalldir = self._conf.get("home_dir")+'/software/'+fullname.split('/')[0]+'/'+fullname.split('/')[-1]+'/easybuild/'
            ebfilepath = moduleinstalldir +'-'.join(fullname.split('/'))+'.eb'
            print(ebfilepath)
            exec(open(ebfilepath).read(),globals(), globals())
            # subprocess.getoutput(ebfilepath)
            dependlist=dependencies +builddependencies
            build_command="the information come from the ebfile which is in install directory "
            # file.close()

            return build_command, dependlist

    def fetchsources(self,*args,**kwargs):
        logger.debug("fetch is the import stage ,so we add the fetch fuction ,\
            if the software is installed ,we can find the sources in sources directory ;\
                and if uninstall ,we can eb --fetch the sources until the source is sucessfully  ")  
        fullname = self.init_package(*args,**kwargs)
        path=self.path
        fetchsourcesflag = 0
        self.load_configure(path)
        # if the module fullname is not installed,then install it !
        if self.check_package(fullname) == False:
            environ = 'GCC'
            build_system = bs.EasyBuild()
            # easyconfigs = ['Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb']
            easyconfigs = [self._ebfilename+'.eb']
            build_system.easyconfigs = easyconfigs
            # options= ['-Dr',"--minimal-toolchains","--try-update-deps","--experimental"]
            fetch_cmd = self._conf.get("fetch_cmd")
            # eb_options = self._conf.get("eb_options")
            eb_options = []
            logger.debug(f"the eb options is {eb_options} ")
            logger.debug(f"the eb options is {fetch_cmd} and the type is {type(fetch_cmd)} ")
            eb_options.insert(0,fetch_cmd)
            logger.debug(f"the options is {eb_options} ")
            build_system.options =  eb_options
            # build_command.prefix = self.install_dir
            build_system.prefix = '/gpfs/fuyun'
            fetch_command = build_system.emit_build_commands("GCC")
            # build_command = 'eb Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb -Dr --minimal-toolchains --try-update-deps --experimental'
            build_system_out = self._run_command(fetch_command)
            logger.debug(f'the fetch out is {build_system_out.stdout}')
            allout1=build_system_out.stdout.split("\n")
            for i,val in enumerate(allout1):
                logger.debug(f'the num is {i} and the value is {val}')
                if val.find("== FAILED: Installation ended unsuccessfully") >=0:
                    logger.debug(f'the fetch sources is failed ,maybe you can download it by hand ')
                    raise ValueError('the fetch sources is failed ,maybe you can download it by hand !')
                    sys.exit(1)
                    # fetchsourcesflag+=1
                
            # logger.debug(f'the value is {fetchsourcesflag}')
            # logger.debug(f'the value is {build_system.prefix}')
            # modulesdir = os.path.join(os.getcwd(), build_system.prefix,
            #                             'modules', 'all')
            # logger.debug(f'the modulefile dir  is {modulesdir}')
            # # with open(build_system_out.stdout) as fp:
            # #     out = fp.read()
            sourceslist = []
            for i in range(len(allout1)):
                m = re.findall(r'INFO Added sources: (.*)', allout1[i])
                if m !=[]:
                    sourceslist.append(m)
                    # sourceslist.append([
                    # {'name': m, 'collection': False, 'path': modulesdir}])
                    # 'ebfile':build_system.prefix+'/software/'+m[0].split('/')[0]+'/'+m[0].split('/')[-1]+'/easybuild/'+'-'.join(m[0].split('/'))+'.eb'}
            logger.debug(f'the sources list  is {sourceslist}')
            # if fetchsourcesflag == 1:
            #     # logger.debug(f'the value is {fetchsourcesflag}')
            #     for i in range(len(allout1)):
            #         # logger.debug(f'the value is {allout1[i]}')
            #         # logger.debug(f'the startswith is {allout1[i].lstrip().startswith("*")}')
            #         # logger.debug(f'the findall is {re.findall(r'module:',allout1[i])}')
            #         if allout1[i].lstrip().startswith("*") and  re.findall(r'module:',allout1[i]) :
            #             # logger.debug(f'the module value is {allout1[i]}')
            #             dependlist.append(allout1[i].split(" ")[-1][:-1])
            #             # logger.debug(f'the value is {fetchsourcesflag}')
            #     logger.debug(f'the depend list  is {dependlist}')
            return sourceslist,fetch_command
        else :
            sourcesdir = self._conf.get("home_dir")+'/sources/'+fullname.split('/')[0][0].lower()+'/'+fullname.split('/')[0]
            fetch_command=["the software is installed before"]
            return sourcesdir,fetch_command


    def install_package(self,*args,**kwargs):
        logger.debug("the install is finish ,you can use it by module load modulename \
                if the check_package(new package) is fail ,to prove the install is fall ")  
        fullname = self.init_package(*args,**kwargs)
        path=self.path
        listdependflag = 0
        self.load_configure(path)
        # if the module fullname is not installed,then install it !
        if self.check_package(fullname) == False:
            environ = 'GCC'
            build_system = bs.EasyBuild()
            # easyconfigs = ['Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb']
            easyconfigs = [self._ebfilename+'.eb']
            build_system.easyconfigs = easyconfigs
            # options= ['-Dr',"--minimal-toolchains","--try-update-deps","--experimental"]
            list_cmd = self._conf.get("build_cmd")
            eb_options = self._conf.get("eb_options")
            logger.debug(f"the eb options is {eb_options} ")
            logger.debug(f"the eb options is {list_cmd} and the type is {type(list_cmd)} ")
            eb_options.insert(0,list_cmd)
            logger.debug(f"the options is {eb_options} ")
            build_system.options =  eb_options
            # build_command.prefix = self.install_dir
            build_system.prefix = '/gpfs/fuyun'
            build_command = build_system.emit_build_commands("GCC")
            # build_command = 'eb Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb -Dr --minimal-toolchains --try-update-deps --experimental'
            build_system_out = self._run_command(build_command)
            logger.debug(f'the install out is {build_system_out.stdout}')
            allout1=build_system_out.stdout.split("\n")
            for i,val in enumerate(allout1):
                logger.debug(f'the num is {i} and the value is {val}')
                if val.find(" COMPLETED: Installation ended successfully") >=0:
                    listdependflag+=1
            logger.debug(f'the value is {listdependflag}')
            logger.debug(f'the value is {build_system.prefix}')
            modulesdir = os.path.join(os.getcwd(), build_system.prefix,
                                        'modules', 'all')
            logger.debug(f'the modulefile dir  is {modulesdir}')
            # with open(build_system_out.stdout) as fp:
            #     out = fp.read()
            _eb_modules = []
            for i in range(len(allout1)):
                m = re.findall(r'building and installing (\S+)...', allout1[i])
                if m != []:
                    logger.debug(f'the module name   is {m}')
                    _eb_modules.append([
                {'name': m[0], 'collection': False, 'path': modulesdir,'ebfile':build_system.prefix+'/software/'+m[0].split('/')[0]+'/'+m[0].split('/')[-1]+'/easybuild/'+'-'.join(m[0].split('/'))+'.eb'}])
                    # _eb_modules.append([
                    # {'name': m, 'collection': False, 'path': modulesdir}])
                    # 'ebfile':build_system.prefix+'/software/'+m[0].split('/')[0]+'/'+m[0].split('/')[-1]+'/easybuild/'+'-'.join(m[0].split('/'))+'.eb'}
            logger.debug(f'the module list  is {_eb_modules}')
            # if listdependflag == 1:
            #     # logger.debug(f'the value is {listdependflag}')
            #     for i in range(len(allout1)):
            #         # logger.debug(f'the value is {allout1[i]}')
            #         # logger.debug(f'the startswith is {allout1[i].lstrip().startswith("*")}')
            #         # logger.debug(f'the findall is {re.findall(r'module:',allout1[i])}')
            #         if allout1[i].lstrip().startswith("*") and  re.findall(r'module:',allout1[i]) :
            #             # logger.debug(f'the module value is {allout1[i]}')
            #             dependlist.append(allout1[i].split(" ")[-1][:-1])
            #             # logger.debug(f'the value is {listdependflag}')
            #     logger.debug(f'the depend list  is {dependlist}')
            return _eb_modules['ebfile'],build_command
        else :
            moduleinstalldir = self._conf.get("home_dir")+'/software/'+fullname.split('/')[0]+'/'+fullname.split('/')[-1]+'/easybuild/'
            ebfilepath = moduleinstalldir +'-'.join(fullname.split('/'))+'.eb'
            eb_command =[]
            str = "test_report.md"
            for filepath in os.listdir(moduleinstalldir):
                if str in filepath:
                    mdfile=moduleinstalldir+filepath
            with open(mdfile) as f :
                key = "* command line:"
                i=0
                for line in f.readlines()[:100]:
                    i+=1
                    if key in line:
                        break
            with open(mdfile) as f :
                key2 = "* full configuration (includes defaults):"
                j=i
                for line in f.readlines()[i:100]:
                    j+=1
                    if key2 in line:
                        break
            for k in range(i+1,j):
                the_line = linecache.getline(mdfile, k)
                eb_command.append(the_line)
                # print(k)
                # print(the_line)
            return ebfilepath,eb_command[1].strip()

    def search_fymodule_file(self,*args,**kwargs):
        """Find templefile match  packages  name (in /gpfs/fuyun/fy_modules and other  /gpfs/fuyun/fy_modules/gemray)."""
        path=self.path
        logger.debug(f'the path dir  is {path}')
        self.load_configure(path)
        software_path = self._conf.get("MoResp_dir")
        templepath  = None
        flag = 0
        name = self.name
        # software_path = "/gpfs/fuyun/fy_modules/physics/" 
        # templefilename = 
        # templefilename = 
        logger.debug(f'the MoResp_dir dir  is {software_path}')
        templefilename = self.modulename +'-'+ self.tag+'.yaml'
        templefilename_sub = self.version +'-'+ self.tag+'.yaml'
        logger.debug(f'the templefilename   is {templefilename}')
        logger.debug(f'the templefilename_sub  is {templefilename_sub}')       

        if Path(software_path).exists() :
            # templepath = Path(tmplefile).parent
            print("ok1")
            if  Path(Path(Path(software_path).joinpath(templefilename))).is_file() :
                print("ok2")
                flag +=1
                # search = Path(Path(Path(software_path).joinpath(name,templefilename)))
                # print(search)
                return flag,Path(Path(Path(software_path).joinpath(templefilename))),templefilename
            elif Path(software_path+'/'+self.name).exists() :
                print("ok3")
                if Path(Path(Path(software_path).joinpath(name,templefilename_sub))).is_file()  :
                    print("ok4")
                # search = Path(Path(Path(software_path).joinpath(name,templefilename)))

                # print(search)
                    flag +=1
                    return flag,Path(Path(Path(software_path).joinpath(name,templefilename_sub)))
                else :
                    print("ok5")

                    return flag,Path(Path(software_path+'/'+self.name)),templefilename_sub
            else :
                print("ok6")
                Path(software_path+'/'+self.name).mkdir()
                return flag,Path(software_path+'/'+self.name),templefilename_sub
        else:
            print("ok7")
            Path(software_path).mkdir()
            return flag,Path(software_path)
        #     raise  RuntimeError('could fount the templefile ,please gime me it  ') 
                
    def search_template_file(self,*args,**kwargs):
        """Find templefile match  packages  name (in /gpfs/fuyun/fy_modules and other  /gpfs/fuyun/fy_modules/gemray)."""
        path=self.path
        logger.debug(f'the path dir  is {path}')
        self.load_configure(path)
        software_path = self._conf.get("MoResp_dir")
        templepath  = None
        flag = 0
        name = self.name
        # software_path = "/gpfs/fuyun/fy_modules/physics/" 
        templefilename = "temple.yaml"
        # templefilename = 
        logger.debug(f'the MoResp_dir dir  is {software_path}')

        if Path(software_path).exists() :
            # templepath = Path(tmplefile).parent
            if  Path(Path(Path(software_path).joinpath(templefilename))).is_file() :
                flag +=1
                # search = Path(Path(Path(software_path).joinpath(name,templefilename)))
                # print(search)
                return flag,Path(Path(Path(software_path).joinpath(templefilename)))
            elif Path(Path(Path(software_path).joinpath(name,templefilename))).is_file()  :
                # search = Path(Path(Path(software_path).joinpath(name,templefilename)))

                # print(search)
                flag +=1
                return flag,Path(Path(Path(software_path).joinpath(name,templefilename)))
            else :
                return flag,Path(software_path)
        else:
            return flag,None
        #     raise  RuntimeError('could fount the templefile ,please gime me it  ') 
        
    def generate_yaml_doc_ruamel(self,yaml_file):
        NAME = self.name
        VERSION = self.version
        TAG = self.tag
        ID = '/actors/physics/genray/'+NAME+'/'+VERSION+'-'+TAG
        DATA = time.ctime()
        ebfile,build_cmd = self.install_package()
        BUILD_CMD = build_cmd
        EBFILE = ebfile
        depend_cmd,denpendlist = self.list_dependence()
        DEPEND_CMD = depend_cmd
        PACKLIST = denpendlist
        PRESCRIPT = [self._conf.get("home_dir")+"/modules/all","module purge","module load"+" "+self.fullname]
        py_object = {'$id': ID,
                    '$schema':  'SpModule#SpModuleLocal',
                    'annotation':{'contributors':'liuxj','date':DATA,'email':'lxj@ipp.ac.cn'},
                    'description':'this is a template file. you can refer this template file to produce your own fy_module file of different packages.  If you have any question ,please connet to liuxj(lxj@ipp.ac.cn)',
                    'homepage':'http://funyun.com/demo.html',
                    'information':{
                        'name':NAME,
                        'version':VERSION

                    },
                    'install':{
                        '$class':'EasyBuild',
                        'process':{
                            'build':{
                                'build_cmd':BUILD_CMD,     
                                'ebfile':EBFILE}
                                },
                            'depend':{
                                'depend_cmd':DEPEND_CMD,
                                'packageslist':PACKLIST},
                            'toolchain':{
                                'tag':TAG},
                                },
                    'license':'GPL',
                    'postscript':'module purge',
                    'prescript': PRESCRIPT,
                    }
        file = open(yaml_file, 'w', encoding='utf-8')
        # yaml=YAML(typ='unsafe', pure=True)
        yaml.dump(py_object, file, Dumper=yaml.RoundTripDumper)
        file.close()


    def deploy(self, **kwargs):
        flag,templefile = self.search_template_file()
        logger.debug(f'the flag and the path  value  is {flag} and {templefile}')
        if flag == 1:
            with open(templefile) as f :
                doc= yaml.load(f,Loader=yaml.FullLoader)
                doc['annotation']['date'] = time.ctime()
                doc['information']['name'] = self.name
                doc['information']['version'] = self.version
                doc['install'][1]['process']['toolchain']['tag'] = self.tag
                depend_cmd,denpendlist = self.list_dependence()
                doc['install'][1]['process']['depend']['depend_cmd'] = depend_cmd
                doc['install'][1]['process']['depend']['packageslist'] = denpendlist
                ebfile,build_cmd = self.install_package()
                doc['install'][1]['process']['build']['budild_cmd'] = build_cmd
                doc['install'][1]['process']['build']['ebfile'] = ebfile
                doc['license'] = "GPL"
                prescript = [self._conf.get("home_dir")+"/modules/all","module purge","module load"+" "+self.fullname]
                doc['prescript'] = prescript
            with open(templefile,'w') as f :
                # yaml=YAML(typ='unsafe', pure=True)
                yaml.dump(doc,f,Dumper=yaml.RoundTripDumper)
            desfile = templefile
        else :
            yaml_path = self._conf.get("MoResp_dir")+"/"+self.name
            if Path(yaml_path).exists() == False :
                Path(yaml_path).mkdir()            
            yaml_name = self.name+".yaml"
            temple_path = os.path.join(yaml_path,yaml_name)
            self.generate_yaml_doc_ruamel(temple_path)
            desfile = temple_path
        return desfile    


    # def listdepend(self, **kwargs):
    #     """[summary]
    #     read form easyconfig dependence :
    #     Returns:
    #         [type]: [description]
    #     """
    #     return ("list the install lib and toolchain ")






