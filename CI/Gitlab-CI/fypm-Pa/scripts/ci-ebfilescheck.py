# -*- coding: utf-8 -*-
import collections
import os
import pathlib
import shlex
import subprocess
import traceback
import uuid
import sys
import unittest
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
import spdm
from spdm.flow.ModuleRepository import ModuleRepository
from spdm.util.logger import logger
import pprint
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/FyBuild/python')
from fypm.ModulePa import ModulePa
from deal_yamlfile import record_variable,record_variable_append,load_templefile

def search_tmple_file(self,*args,**kwargs):
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
def generate_yaml_doc_ruamel(self,yaml_file):
    NAME = self.name
    VERSION = self.version
    TAG = self.tag
    ID = '/actors/physics/genray/'+NAME+'/'+VERSION+'-'+TAG
    DATA = time.ctime()
    ebfile,build_cmd = self.installpa()
    BUILD_CMD = build_cmd
    EBFILE = ebfile
    depend_cmd,denpendlist = self.listdepend()
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
    flag,templefile = self.search_tmple_file()
    logger.debug(f'the flag and the path  value  is {flag} and {templefile}')
    if flag == 1:
        with open(templefile) as f :
            doc= yaml.load(f,Loader=yaml.FullLoader)
            doc['annotation']['date'] = time.ctime()
            doc['information']['name'] = self.name
            doc['information']['version'] = self.version
            doc['install'][1]['process']['toolchain']['tag'] = self.tag
            depend_cmd,denpendlist = self.listdepend()
            doc['install'][1]['process']['depend']['depend_cmd'] = depend_cmd
            doc['install'][1]['process']['depend']['packageslist'] = denpendlist
            ebfile,build_cmd = self.installpa()
            doc['install'][1]['process']['build']['budild_cmd'] = build_cmd
            doc['install'][1]['process']['build']['ebfile'] = ebfile
            doc['license'] = "GPL"
            prescript = [self._conf.get("home_dir")+"/modules/all","module purge","module load"+" "+self.fullname]
            doc['prescript'] = prescript
        with open(templefile,'w') as f :
            # yaml=YAML(typ='unsafe', pure=True)
            yaml.dump(doc,f,Dumper=yaml.RoundTripDumper)
    else :
        yaml_path = self._conf.get("MoResp_dir")+"/"+self.name
        yaml_name = self.name+".yaml"
        temple_path = os.path.join(yaml_path,yaml_name)
        self.generate_yaml_doc_ruamel(temple_path)