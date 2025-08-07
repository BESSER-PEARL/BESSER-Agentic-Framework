class A2ARouter:
    def __init__(self):
        self.methods = {}

    def register(self, method_name, func):
        self.methods[method_name] = func

    def handle(self, method_name, params):
        if method_name not in self.methods:
            raise Exception(f"Method '{method_name}' not found")
        return self.methods[method_name](**params)
