import json

from spanish.models import ALL_MODELS

if __name__ == "__main__":
    print(json.dumps(ALL_MODELS, ensure_ascii=False, indent=2))
