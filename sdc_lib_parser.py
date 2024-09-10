import ast

def strip_library_name(library):
    # Remove the prefix and suffix
    return library.replace("streamsets-datacollector-", "").replace("-lib:5.12.0", "")

# Stage lib for SDC
with open('config/sdc/sdc_stage_libs.txt', 'r') as file:
    libraries = file.read()
libraries = ast.literal_eval(libraries)

stripped_libraries = [strip_library_name(lib) for lib in libraries]
with open('config/sdc/sdc_stage_libs.conf', 'w') as file:
    for index, item in enumerate(libraries):
        stripped_name = strip_library_name(item)
        if index < len(libraries) - 1:
            file.write(stripped_name + '\n')
        else:
            file.write(stripped_name)  # No newline after the last item
print("Stage lib list written to sdc_stage_libs.conf")

