import math, hashlib, json
р = {}
xs = [i / 997.0 for i in range(1, 20000)]
def h(vals): return hashlib.md5(repr(vals).encode()).hexdigest()[:10]
р['pow_1/2.4'] = h([x ** (1 / 2.4) for x in xs])
р['pow_2.4'] = h([x ** 2.4 for x in xs])
р['cbrt_pow1/3'] = h([x ** (1 / 3) for x in xs])
р['atan2'] = h([math.atan2(x - 10, 7 - x) for x in xs])
р['sin'] = h([math.sin(x) for x in xs]); р['cos'] = h([math.cos(x) for x in xs])
р['exp'] = h([math.exp(x / 3) for x in xs]); р['log'] = h([math.log(x) for x in xs])
р['hypot'] = h([math.hypot(x, 3.3) for x in xs]); р['sqrt'] = h([math.sqrt(x) for x in xs])
р['degrees_atan2'] = h([math.degrees(math.atan2(x, 1.7)) for x in xs])
р['pow_7'] = h([x ** 7 for x in xs]); р['pow_25_7'] = h([(x**7 / (x**7 + 25**7)) ** 0.5 for x in xs])
print(json.dumps(р))
