import sys, os, json
os.chdir(sys.argv[1]); sys.path.insert(0, os.getcwd())
import мовний_шар as МШ
cases = [("Новорічна вечірка в ресторані, надворі мороз", dict(occasion="celebration", place="restaurant_upscale", weather_feel="frost", part_of_day="evening", quotes=dict(occasion="Новорічна вечірка в ресторані", place="ресторані", weather_feel="мороз"))),
 ("завтра на роботу пішки, обіцяють можливо дощ", dict(occasion="work", precipitation="possible_rain", quotes=dict(occasion="на роботу", precipitation="обіцяють можливо дощ", weather_feel="обіцяють можливо дощ"))),
 ("завтра на роботу пішки, обіцяють можливо дощ", dict(occasion="work", weather_feel="possible_rain", quotes=dict(occasion="на роботу", weather_feel="обіцяють можливо дощ")))]
for сл, в in cases:
    try:
        п = МШ.паспорт_з_шару(в, {}, None, None, слова_ходу=сл)["паспорт"]
        print({k: п.get(k) for k in ("година","темп_c","опади")}, {k:v for k,v in п.items() if "погод" in k or "weather" in k})
    except Exception as e:
        print("ERR", repr(e)[:300])
