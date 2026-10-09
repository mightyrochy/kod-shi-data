# -*- coding: utf-8 -*-
"""Рядок 1998: описи фасаду й межі відтворюваності відповідають коду."""
import os

корінь = os.path.dirname(os.path.dirname(__file__))
читати = lambda н: open(os.path.join(корінь, н), encoding="utf-8").read()
print("composer: «мінімізує» ×", читати("composer.py").count("мінімізує"))
print("coordination: «ПІДЛОГА шуму» ×", читати("coordination.py").count("ПІДЛОГА шуму"),
      "«ВЕРХНЯ МЕЖА» ×", читати("coordination.py").count("ВЕРХНЯ МЕЖА"))
