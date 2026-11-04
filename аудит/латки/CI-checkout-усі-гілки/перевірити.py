"""Виконує скрипт саме з латки на копіях репозиторію з контрольованою історією."""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

ТУТ = pathlib.Path(__file__).resolve().parent


def команда(*аргументи, тека=None, середовище=None, вхід=None):
    """Виконує команду й зупиняє перевірку на будь-якій відмові."""
    return subprocess.run(
        аргументи, cwd=тека, env=середовище,
        input=вхід.encode("utf-8") if вхід is not None else None,
        capture_output=True, check=True,
    ).stdout.decode("utf-8").strip()


def перевірити(баш, тека):
    """Перевіряє голову, базу, давню історію та відсутність чужих об'єктів."""
    тека.mkdir(parents=True, exist_ok=False)
    джерело = тека / "origin.git"
    команда("git", "init", "--bare", "--initial-branch=main", str(джерело))
    команда("git", "config", "user.name", "Перевірка", тека=джерело)
    команда("git", "config", "user.email", "checkout@example.invalid", тека=джерело)
    вміст = команда("git", "hash-object", "-w", "--stdin", тека=джерело, вхід="давній файл\n")
    дерево = команда("git", "mktree", тека=джерело, вхід=f"100644 blob {вміст}\thistory.txt\n")
    чужий_вміст = команда("git", "hash-object", "-w", "--stdin", тека=джерело, вхід="сторонній запис" * 100000)
    чуже_дерево = команда("git", "mktree", тека=джерело, вхід=f"100644 blob {чужий_вміст}\tforeign.txt\n")

    def коміт(назва, *батьки, дерево=дерево):
        """Будує граф, включно з незлитою гілкою, без зайвих файлів."""
        аргументи = ["git", "commit-tree", дерево, "-m", назва]
        for батько in батьки:
            аргументи += ["-p", батько]
        return команда(*аргументи, тека=джерело)

    давній = коміт("давня база проб")
    спільний = коміт("спільний предок", давній)
    база = коміт("базовий main", спільний)
    голова = коміт("голова PR", спільний)
    злиття = коміт("тестове злиття PR", база, голова)
    чужий = коміт("чужа незлита гілка", дерево=чуже_дерево)
    for посилання, ша in (("refs/heads/main", база), ("refs/heads/feature", голова),
                         ("refs/pull/1/merge", злиття), ("refs/heads/gemini/foreign", чужий),
                         ("refs/tags/foreign", чужий)):
        команда("git", "update-ref", посилання, ша, тека=джерело)

    латка = (ТУТ / "checkout.patch").read_text(encoding="utf-8")
    частина = латка.split("+++ b/.github/scripts/checkout-history.sh\n", 1)[1]
    скрипт = тека / "checkout-history.sh"
    скрипт.write_text("".join(рядок[1:] for рядок in частина.splitlines(True)
                             if рядок.startswith("+")), encoding="utf-8", newline="\n")
    команда(баш, "-n", str(скрипт))
    контроль = тека / "baseline"
    команда("git", "init", str(контроль))
    команда("git", "remote", "add", "origin", джерело.as_uri(), тека=контроль)
    команда("git", "fetch", "origin", "+refs/heads/*:refs/remotes/origin/*",
            "+refs/tags/*:refs/tags/*", тека=контроль)
    команда("git", "cat-file", "-e", чужий, тека=контроль)
    команда("git", "cat-file", "-e", чужий_вміст, тека=контроль)
    до = {"чужа_гілка": True, "чужий_об’єкт": True,
          "тегів": len(команда("git", "tag", тека=контроль).splitlines())}
    звіт = []
    випадки = [("PR merge", злиття, база), ("PR head", голова, база),
               ("push", база, спільний), ("ручний запуск", база, ""),
               ("нульова база", база, "0" * 40), ("автентифікація", злиття, база)]
    for номер, (назва, ша, базовий) in enumerate(випадки):
        копія = тека / f"copy-{номер}"
        команда("git", "init", str(копія))
        команда("git", "remote", "add", "origin", джерело.as_uri(), тека=копія)
        # Навмисно широкий remote.origin.fetch: явні refspec мусять його звузити.
        команда("git", "fetch", "--no-tags", "--depth=1", "origin", ша, тека=копія)
        команда("git", "checkout", "--detach", "FETCH_HEAD", тека=копія)
        assert команда("git", "rev-parse", "--is-shallow-repository", тека=копія) == "true"
        середовище = {ключ: значення for ключ, значення in os.environ.items()
                      if ключ not in {"GITHUB_TOKEN", "GH_TOKEN"}}
        середовище.update(GITHUB_SHA=ша, BASE_REF=базовий)
        if назва == "автентифікація":
            середовище["GITHUB_TOKEN"] = "fixture-token"
        початок = time.monotonic()
        for повтор in range(2):
            команда(баш, str(скрипт), тека=копія, середовище=середовище)
            assert команда("git", "rev-parse", "HEAD", тека=копія) == ша
            assert команда("git", "rev-parse", "origin/main", тека=копія) == база
            assert команда("git", "rev-parse", "--is-shallow-repository", тека=копія) == "false"
            команда("git", "cat-file", "-e", давній, тека=копія)
            assert команда("git", "show", давній + ":history.txt", тека=копія) == "давній файл"
            команда("git", "cat-file", "-e", (базовий if базовий.strip("0") else база), тека=копія)
            assert команда("git", "merge-base", ша, база, тека=копія) == (спільний if ша == голова else база)
            assert not команда("git", "tag", тека=копія)
            assert команда("git", "for-each-ref", "--format=%(refname)", "refs/remotes", тека=копія) == "refs/remotes/origin/main"
            процес = subprocess.run(["git", "cat-file", "-e", чужий], cwd=копія, capture_output=True)
            assert процес.returncode != 0, "Завантажено об'єкт чужої гілки"
            процес = subprocess.run(["git", "cat-file", "-e", чужий_вміст], cwd=копія, capture_output=True)
            assert процес.returncode != 0, "Завантажено blob чужої гілки"
            assert "extraheader" not in команда("git", "config", "--local", "--list", тека=копія).lower()
        звіт.append({"випадок": назва, "повторів": 2, "секунд": round(time.monotonic() - початок, 3),
                     "чужих_гілок": 0, "чужих_об’єктів": 0, "тегів": 0, "давня_база": True})
    результат = json.dumps({"до": до, "після": звіт}, ensure_ascii=False, indent=2)
    (ТУТ / "локальна_перевірка.json").write_text(результат + "\n", encoding="utf-8")
    print(результат)


if __name__ == "__main__":
    перевірити(sys.argv[1], pathlib.Path(tempfile.mkdtemp(prefix="checkout-", dir=os.environ["TEMP"])) / "стенд")
