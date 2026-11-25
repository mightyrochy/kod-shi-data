"""One-shot offline repair builder. This does not execute a scene or call a transport."""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import pickle
import socket
import subprocess
from unittest.mock import patch

from archive_inputs import load_dir, records, answer
from ядро import пул, річ, розбір, суд, запит, знання
from ядро.перекладач_паспорта import з_входу, підготувати_портрет_і_палітру
from ядро.поняття import Збій

HERE = Path(__file__).resolve().parent
ARCHIVE_SHA = '224bf4efc78c21e35d904963d1e8c6b820ec3545'
CODE_SHA = '38f3a7952bec9700eff6f50a51f993238d923bf0'
LIMIT = 25_334

def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()

def blocked(*args, **kwargs):
    raise RuntimeError("network disabled")
socket.socket = socket.getaddrinfo = socket.create_connection = blocked

def dump(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
def checksum(b):
    return sha256(b).hexdigest()
def artifact(path):
    return {"path": str(path), "blob": git('rev-parse', f'{ARCHIVE_SHA}:{path}'),
            "sha256": checksum(path.read_bytes())}
def write(name, data):
    (HERE/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def byte_len(text):
    return len(text.encode('utf-8'))

CATALOGUE = pickle.loads((HERE/'catalogue.pkl').read_bytes())
BY_ID = {x['id']: x for x in CATALOGUE}

def case(scene, repair_index, assembly_index):
    label = scene.split('_')[0]
    directory, exchanges, tracefile, trace, handsfile, _ = load_dir(scene)
    case = next(x for x in records(scene) if x[0]==repair_index)
    _, atlas, look, compatible, chosen, seed = case
    assert assembly_index in compatible and len(atlas)==1
    assert any(score[2]==score[3]==score[4] for score in chosen), chosen
    atlas_label, oldmap=atlas[0]
    old_exchange, old_request, old_repair, old_line = exchanges[repair_index]
    assembly_exchange, _, _, assembly_line = exchanges[assembly_index]
    stocked = {oldmap[n] for ids in look.values() for n in ids}
    source = trace['прогони'][0]['спільне']
    saved_input = {"профіль": source["вхід_прогону"], "паспорт": source["паспорт"], "сід": seed}
    profile = знання.профіль_суду(saved_input['профіль'])
    features, palette = підготувати_портрет_і_палітру(saved_input)
    situation = з_входу(saved_input, план_палітри=palette, риси_портрета=features)
    report = {"repair_archive_index_zero_based": repair_index,
              "assembly_archive_index_zero_based": assembly_index, "recorded_build": trace['спільне']['збірка'],
              "archive": artifact(directory/'обміни.jsonl'), "trace": artifact(tracefile), "hands": artifact(handsfile),
              "repair_line_sha256": checksum(old_line), "assembly_line_sha256": checksum(assembly_line),
              "profile_pasport_seed_sha256": checksum(dump(saved_input).encode()),
              "address_atlas_legacy_label": atlas_label, "hand_1_confirmation": chosen,
              "archive_image_count": sum(1 for msg in old_request['messages'] for b in msg['content'] if b['type']=='image_url'),
              "archive_look_ids": list(look), "archive_stocks": len(stocked),
              "archive_candidates": len(old_repair['candidates']['rows']),
              "archive_repair_reserve": old_request['max_tokens']}
    legacy_kept = [r for r in old_repair['candidates']['rows'] if r[0] in {n for a in look.values() for n in a}]
    if len(legacy_kept)==len(stocked):
        legacy_body=deepcopy(old_repair)
        legacy_body['candidates']['rows']=legacy_kept
        legacy_body['showcase']=[]
        legacy_text=dump(legacy_body)
        estimate=знання.палітрові_знання().оцінити_текст_ядра
        report['archive_only_compare']={"minimum_json_bytes_compact":byte_len(legacy_text),
                "minimum_json_tokens_estimate":estimate(legacy_text),
                "findings_total":sum(len(v['findings']) for v in old_repair['verdict']),
                "note":"Independent archival compact JSON comparison; different legacy stage wire."}
    report["missing_catalogue_ids"] = sorted(stocked - BY_ID.keys())
    present = {i: BY_ID[i] for i in stocked if i in BY_ID}
    report["present_catalogue_rows"] = len(present)
    # Use the current catalog's actual entry points and report any earlier admission blocker.
    stock = пул.зібрати(situation, 1, seed, CATALOGUE, профіль=profile)
    addr={r['ід']:r['н'] for r in stock.речі}
    report['current_pool_rows']=len(addr)
    report['upstream_exclusions']=[{'id':x['ід'],'reason':x['причина'],'boundary':x['межа'],
                                     'diagnostic_fields':[z['поле'] for z in x.get('заяви',())]}
                                    for x in stock.відкинуто if x['ід'] in stocked]
    unresolved=stocked-addr.keys()
    report['upstream_missing_ids']=sorted(unresolved)
    write(label+'-upstream.json',report)
    if unresolved:
        if report["missing_catalogue_ids"]:
            return report
        # Keep the exact archived compositions. Test the stage on a catalogue
        # restricted to those same authenticated records, with normal Ch3 rules.
        restricted = пул.зібрати(situation, 1, seed, list(present.values()), профіль=profile)
        addr_restricted = {r['ід']: r['н'] for r in restricted.речі}
        report['restricted_pool_admitted'] = len(addr_restricted)
        report['restricted_pool_rejects'] = [{k: x[k] for k in ('ід','межа','причина')}
                                              for x in restricted.відкинуто]
        if stocked <= addr_restricted.keys():
            stock, addr = restricted, addr_restricted
            report['measurement_mode'] = 'pinned_archive_catalogue_with_native_ch3'
        else:
            # Pure Ch4 input fixture: the archived repair already contains the
            # exact mandatory items. Keep full-pool admitted ranks, and resolve
            # excluded archived items via the normal reader without invented ranks.
            report['measurement_mode'] = 'direct_ch4_archived_pool_fixture_upstream_blocks'
            maps = dict(stock.записи)
            rows = list(stock.речі)
            for i in sorted(unresolved):
                n = next(n for n, key in oldmap.items() if key == i)
                new = f'@архів{n}'
                assert new not in maps
                record = річ.читати(present[i])
                if record.збої:
                    report['fixture_invalid_record'] = {'id': i, 'failures': [z.в_json() for z in record.збої]}
                    return report
                maps[new] = record
                rows.append({"н": new, "ід": i, "ранг": None, "джерело_рангу": (),
                             "за": None, "факти_рангу": {}})
                addr[i] = new
            stock = replace(stock, речі=tuple(rows), записи=maps)
    else:
        report['measurement_mode'] = 'native_ch3_archived_pinned_rows'
    old_looks={a['id']: a for a in answer(assembly_exchange)['outfits']}
    current_reply=[]
    archived_compositions={}
    for number, nums in look.items():
        prev=deepcopy(old_looks[number])
        assert prev['items']==nums
        n_to_id={n:oldmap[n] for n in nums}
        archived_compositions[number]=[n_to_id[n] for n in nums]
        prev['items']=[addr[n_to_id[n]] for n in nums]
        for block in ('deliberate','worn'):
            for statement in prev.get(block,[]):
                statement['item']=addr[n_to_id[statement['item']]]
        current_reply.append(prev)
    compositions=розбір.прочитати({"текст":dump({"version":"1","outfits":current_reply})},"складання",stock)
    if isinstance(compositions,Збій):
        report['pre_repair_failure']=compositions.в_json()
        return report
    assert {a.ід:[r['ід'] for r in a.речі] for a in compositions}==archived_compositions
    verdicts={a.ід:суд.судити(a,situation,stock,profile) for a in compositions}
    report['verdict_failures']={n:v.в_json() for n,v in verdicts.items() if isinstance(v,Збій)}
    if report['verdict_failures']:
        return report
    report.update(compositions=archived_compositions,
                  findings_by_outfit={n:len(v.заяви) for n,v in verdicts.items()},
                  repair_trigger_outfits=[n for n,v in verdicts.items() if суд.потребує_ремонту(v)])
    write(label+'-verdicts.json', {n:v.в_json() for n,v in verdicts.items()})
    # Retain the stock path's absolute minimum from the builder. Input is the confirmed
    # archived placed rows; the optional original 24 roster numbers have no ID map.
    candidates = set(addr[i] for i in stocked)
    original = запит._під_вікно
    captures=[]
    def captured(body, field, rows, groups, pinned, limit, estimate, update):
        first=[]
        def see(text):
            if not first:
                first.append(text)
            return estimate(text)
        result=original(body, field, rows, groups, pinned, limit, see, update)
        captures.append((set(rows), set(pinned), first[0], result))
        return result
    model={"вихід":old_request['max_tokens']}
    with patch.object(запит,'_під_вікно',captured):
        out=запит.запит('ремонт',stock,situation,profile,образи=compositions,вироки=verdicts,
                         дозволені=candidates, модель=model)
    if not captures:
        report['pre_repair_failure']=out.в_json()
        return report
    eligible,pins,minimum,(delivered,chosen_rows)=captures[0]
    body=json.loads(minimum)
    assert len(body['verdict'])==len(compositions)
    report['minimum_wire_sha256']=checksum(minimum.encode())
    (HERE/(label+'-minimum.json')).write_text(minimum,encoding='utf-8')
    result=out.розмір if not isinstance(out,Збій) else out.дані
    if isinstance(out,Збій):
        report['structured_failure']=out.в_json()
    estimate=знання.палітрові_знання().оцінити_текст_ядра
    reserve=result['response_reserved_tokens']
    text_est=estimate(minimum)
    photos=result['photo_tokens_estimate']
    labels=result['photo_label_tokens_estimate']
    total=text_est+labels+photos+reserve
    assert result['limit_tokens']==LIMIT
    report['minimum']={"pinned":len(pins),"additional":len(eligible-pins),"json_utf8_bytes":byte_len(minimum),
                       "joint_json_tokens_estimate":text_est,"photo_count":result['photo_count'],
                       "photo_label_tokens_estimate":labels,"photo_tokens_estimate":photos,"reserve":reserve,
                       "total":total,"deficit":max(total-LIMIT,0),"headroom":max(LIMIT-total,0),
                       "candidate_stage_limit":LIMIT,"non_additive_sections":{k:{
                           "standalone_utf8_bytes":byte_len(dump({k:v})),
                           "standalone_estimate":estimate(dump({k:v}))} for k,v in body.items()}}
    if not isinstance(out,Збій):
        report['under_limit_result']=result
    return report

assert git('rev-parse','HEAD')==CODE_SHA and not git('status','--porcelain')
all_reports={"code_sha":CODE_SHA, "archive_sha":ARCHIVE_SHA, "catalogue_gzip_blob":git(
             'rev-parse',f'{CODE_SHA}:каталог_повний.xml.gz'),"catalogue_records":len(CATALOGUE),
             "cases":{}}
for scene,repair,assembly in [('с8_мінус_десять_сніг',17,14),('с3_дощ_замшеві_чоботи',16,12)]:
    report=case(scene,repair,assembly)
    all_reports['cases'][scene]=report
    write('budget-report.json',all_reports)
    print(scene, {k: v for k,v in report.items() if k in (
        'archive_stocks','current_pool_rows','upstream_missing_ids','pre_repair_failure','minimum','verdict_failures')}, flush=True)
