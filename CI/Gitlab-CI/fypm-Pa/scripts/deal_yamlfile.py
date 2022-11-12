from ruamel import yaml
def record_variable(yaml_file,py_object):
    file = open(yaml_file, 'w', encoding='utf-8')
    # yaml=YAML(typ='unsafe', pure=True)
    yaml.dump(py_object, file, Dumper=yaml.RoundTripDumper)
    file.close()
def record_variable_append(yaml_file,py_object):
    file = open(yaml_file, 'a', encoding='utf-8')
    # yaml=YAML(typ='unsafe', pure=True)
    yaml.dump(py_object, file, Dumper=yaml.RoundTripDumper)
    file.close()
def load_templefile(yaml_file):
    file = open(yaml_file, 'r', encoding='utf-8')
    return yaml.safe_load(file) 
    file.close()