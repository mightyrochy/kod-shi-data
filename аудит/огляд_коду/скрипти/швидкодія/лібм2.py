import math, json
xs = [i / 997.0 for i in range(1, 20000)]
р = {'pow_1/2.4': [x ** (1 / 2.4) for x in xs], 'pow_1/3': [x ** (1 / 3) for x in xs],
     'atan2': [math.atan2(x - 10, 7 - x) for x in xs], 'cos': [math.cos(x) for x in xs],
     'exp': [math.exp(x / 3) for x in xs], 'pow_7': [x ** 7 for x in xs]}
print(json.dumps({k: [v.hex() for v in vs] for k, vs in р.items()}))
