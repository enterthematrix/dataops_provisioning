import ast
import re

def strip_library_name(library):
    # Remove the prefix and suffix
    library = library.replace("streamsets-transformer-", "")
    return re.sub(r"-lib:[^\s]+", "",library)

# Stage lib for SDC
with open('config/transformer/transformer_stage_libs.txt', 'r') as file:
    libraries = file.read()
libraries = ast.literal_eval(libraries)

stripped_libraries = [strip_library_name(lib) for lib in libraries]
with open('config/transformer/transformer_stage_libs.conf', 'w') as file:
    for index, item in enumerate(libraries):
        stripped_name = strip_library_name(item)
        if index < len(libraries) - 1:
            file.write(stripped_name + '\n')
        else:
            file.write(stripped_name)  # No newline after the last item
print("Stage lib list written to transformer_stage_libs.conf")

