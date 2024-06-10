import os
import importlib.util

def load_api(path):
    api_spec = importlib.util.spec_from_file_location(os.path.basename(path), path)
    api = importlib.util.module_from_spec(api_spec)
    api_spec.loader.exec_module(api)

    return api

def load_apis():
    apis = []
    for dir in ['api']:
        if os.path.exists(dir):
            for apipy in os.listdir(dir):
                if not apipy.endswith('.py'):
                    continue
                if not os.path.isfile(f"{dir}/{apipy}"):
                    continue

                try:
                    api = load_api(f"{dir}/{apipy}")
                    apis.append(api)
                except Exception as e:
                    print(f"Error loading {dir}/{apipy}")
                    print(repr(e))

    return apis
