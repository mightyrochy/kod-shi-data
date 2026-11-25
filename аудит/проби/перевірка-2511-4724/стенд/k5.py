import sys, json
sys.path.insert(0, sys.argv[1])
import мовний_шар as М
з=dict(occasion=dict(label='вечірка на день народження подруги, субота ввечері', quote='вечірка на день народження подруги, субота ввечері', source='her'))
р=[dict(about=['occasion'], recorded=['occasion'], her_words=['вечірка на день народження подруги'], says='Вечірка на день народження подруги, субота ввечері. Куди ти збираєшся?')]
print(json.dumps(М.суд_репліки(р, dict(recorded=з)), ensure_ascii=False, default=str)[:600])
print(json.dumps(М.суд_речень_репліки(р, dict(recorded=з)), ensure_ascii=False, default=str)[:600])
