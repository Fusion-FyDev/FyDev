from ruamel import yaml
import os
import time
def generate_yaml_doc_ruamel(yaml_file):
    from ruamel import yaml
    NAME="GENRAY"
    VERSION = '10.3'
    TAG = 'foss-2020a'
    ID = '/actors/physics/genray/'+NAME+'/'+VERSION+'-'+TAG
    DATA = time.ctime()
    BUILD_CMD = 'eb genray-mpi-201213-gompi-2020a.eb -l --force --robot --minimal-toolchains'
    EBFILE = '/gpfs/fuyun//software/genray-mpi/201213-gompi-2020a/easybuild/genray-mpi-201213-gompi-2020a.eb'
    DEPEND_CMD = 'eb genray-mpi-201213-gompi-2020a.eb -l --force --robot --minimal-toolchains'
    PACKLIST = ['name1','name2']
    PRESCRIPT = ['module use /fuyun/modules/all','module purge','module load {name}}/{version}{tag}']
    print(ID)
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
    yaml.dump(py_object, file, Dumper=yaml.RoundTripDumper)
    file.close()
current_path = os.path.abspath(".")
yaml_path = os.path.join(current_path, "generate.yaml")
generate_yaml_doc_ruamel(yaml_path)