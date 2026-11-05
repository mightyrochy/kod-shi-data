"""Вимірює сталу частину verdict_comment тим самим способом, що чинний прилад промптів."""
from pathlib import Path
import json
import sys
корінь = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(корінь / 'джерела'), str(корінь / 'джерела/прилади')]
import мовний_шар as м
import корінь_е2_промпти as п


def main():
    """Друкує довжину оголошення та описи полів без виклику моделі."""
    оголошення = м.ОГОЛОШЕННЯ_ВХОДУ['verdict_comment']
    текст = json.dumps(п.повне_оголошення(оголошення), ensure_ascii=False).replace('<дані>', '')
    print(json.dumps({'довжина': len(текст), 'межа_наряду': 5641,
                      'items': м.ВИДИ_ВХОДУ['verdict_comment']['вхід'][0],
                      'about_items.id': м.ВИДИ_ВХОДУ['verdict_comment']['опис']['about_items.id']},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
