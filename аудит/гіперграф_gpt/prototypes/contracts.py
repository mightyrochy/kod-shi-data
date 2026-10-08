"""Write the proposal's concrete minimal JSON contract and a synthetic instance."""
import json
from pathlib import Path
import jsonschema

ROOT=Path('/workspace/liusterko-hypergraph-gpt-e70c3c3')
def obj(properties,required=None):
    return {'type':'object','properties':properties,'required':required or list(properties),'additionalProperties':False}
string={'type':'string','minLength':1}
strings={'type':'array','items':string}
number={'type':'number'}
enum=lambda *xs: {'enum':list(xs)}
ref=lambda name: {'$ref':'#/$defs/'+name}
arr=lambda name: {'type':'array','items':ref(name)}

defs={
 'node':obj({'id':string,'revision':{'type':'integer','minimum':1},'type':enum('item_model','variant','owned_item','placement','body_zone','person_state','scene','intent','outfit','rule'),
             'ref':{'type':['string','null']}}),
 'domain':obj({'kind':enum('point','interval','finite_set','arc_union','missing','conflict'),
               'value':{},'unit':string,'coordinate_system':string,'joint_domain_ref':{'type':['string','null']}},['kind','value','unit','coordinate_system','joint_domain_ref']),
 'evidence':obj({'id':string,'kind':enum('measurement','self_report','merchant_claim','model_interpretation','convention','derived'),
                 'source_ref':string,'source_revision':string,'method':string,'calibration_ref':{'type':['string','null']},
                 'lineage':strings,'scope':string}),
 'fact':obj({'id':string,'subject':string,'field':string,'revision':{'type':'integer','minimum':1},
             'domain':ref('domain'),'evidence_ids':strings,'epistemic_state':enum('observed','inferred','assumed','missing','conflicting')}),
 'binding':obj({'role':string,'node_ids':strings,'symmetric':{'type':'boolean'}}),
 'factor':obj({'id':string,'rule_id':string,'rule_revision':string,'evaluator':string,'bindings':arr('binding'),
               'scene_id':string,'intent_id':string,'read_set':strings,'guard_read_set':strings,
               'membership_read_set':strings,'evidence_ids':strings}),
 'input_version':obj({'ref':string,'revision':{'type':'integer','minimum':0}}),
 'metric':obj({'name':string,'domain':ref('domain'),'scale_kind':enum('physical','ordinal','predicate','uncalibrated_proxy'),
               'polarity':enum('observation','supports','concerns','neutral'),
               'probability_model_ref':{'type':['string','null']}}),
 'evaluation':obj({'id':string,'factor_id':string,'outfit_revision':string,'input_versions':arr('input_version'),
                   'applicability':enum('true','false','unknown'),
                   'execution':enum('complete','partial','not_run','error','legacy_opaque'),
                   'outcome':enum('satisfied','violated','indeterminate','supports','neutral','mixed','unknown','not_applicable','conflict'),
                   'metrics':arr('metric'),'missing_refs':strings,'derived_from':strings,
                   'error_code':{'type':['string','null']}}),
 'decision':obj({'id':string,'author':enum('human','stylist','legacy_policy'),
                 'state':enum('proposed','accepted','rejected','withdrawn'),
                 'type':enum('pin','veto','accept_deviation','prefer','select'),
                 'target_refs':strings,'scope':string,'reason_ref':string,'revision':{'type':'integer','minimum':1}}),
 'placement':obj({'id':string,'item_ref':string,'part_ref':{'type':['string','null']},'roles':strings,'covers':strings,
                  'wear_state_ref':string}),
 'outfit':obj({'id':string,'revision':string,'scene_ids':strings,'placements':arr('placement'),
               'membership_revision':{'type':'integer','minimum':1},'decision_ids':strings}),
}
defs['domain']['allOf']=[
 {'if':{'properties':{'kind':{'const':'interval'}}},'then':{'properties':{'value':{'type':'array','items':number,'minItems':2,'maxItems':2}}}},
 {'if':{'properties':{'kind':{'const':'missing'}}},'then':{'properties':{'value':{'type':'null'}}}},
 {'if':{'properties':{'kind':{'enum':['finite_set','conflict','arc_union']}}},'then':{'properties':{'value':{'type':'array','minItems':1}}}},
]
schema=obj({'schema_version':{'const':'lyusterko.interaction/0.1-proposal'},'synthetic':{'type':'boolean'},
            'nodes':arr('node'),'evidence':arr('evidence'),'facts':arr('fact'),'factors':arr('factor'),
            'evaluations':arr('evaluation'),'decisions':arr('decision'),'outfits':arr('outfit')})
schema.update({'$schema':'https://json-schema.org/draft/2020-12/schema','$defs':defs,
               'title':'Liusterko interaction core — research contract, not accepted product protocol'})

domain=lambda k,v,u='1',cs='declared_predicate':dict(kind=k,value=v,unit=u,coordinate_system=cs,joint_domain_ref=None)
nodes=[dict(id=i,revision=1,type=t,ref=None) for i,t in [('owned:trousers','owned_item'),('variant:top','variant'),
       ('p:top','placement'),('p:lower','placement'),('scene:gallery','scene'),('intent:waist','intent'),('outfit:1','outfit'),('rule:anchor@1','rule')]]
evidence=[dict(id='e:user:1',kind='self_report',source_ref='synthetic:user-utterance-1',source_revision='1',method='explicit request',
               calibration_ref=None,lineage=['synthetic'],scope='scene:gallery'),
          dict(id='e:rule:1',kind='convention',source_ref='proposal:volume-anchor-example',source_revision='1',method='hypothesis',
               calibration_ref=None,lineage=['synthetic'],scope='intent:waist')]
facts=[dict(id='fact:'+f,subject='outfit:1',field=f,revision=1,domain=domain(k,v),evidence_ids=['e:user:1'],epistemic_state=st)
       for f,k,v,st in [('upper.volume','finite_set',[1],'inferred'),('lower.volume','finite_set',[1],'inferred'),
                        ('anchor.visible','missing',None,'missing'),('intent.waist','finite_set',[True],'observed')]]
facts += [dict(id='fact:wear:'+who,subject='p:'+who,field='wear_state',revision=1,
               domain=domain('finite_set',['as_described']),evidence_ids=['e:user:1'],epistemic_state='observed') for who in ['top','lower']]
factor=dict(id='factor:anchor:1',rule_id='rule:anchor@1',rule_revision='1',evaluator='volume_anchor_v1',
            bindings=[dict(role='upper',node_ids=['p:top'],symmetric=False),dict(role='lower',node_ids=['p:lower'],symmetric=False)],
            scene_id='scene:gallery',intent_id='intent:waist',read_set=[f['id'] for f in facts[:3]],guard_read_set=['fact:intent.waist'],
            membership_read_set=['outfit:1.membership'],evidence_ids=['e:rule:1'])
evaluation=dict(id='eval:anchor:1',factor_id=factor['id'],outfit_revision='1',input_versions=[dict(ref=f['id'],revision=1) for f in facts[:4]]+[dict(ref='outfit:1.membership',revision=1)],
                applicability='true',execution='partial',outcome='unknown',
                metrics=[dict(name='unanchored_volume',domain=domain('interval',[0,1]),scale_kind='predicate',polarity='concerns',probability_model_ref=None),
                         dict(name='anchored_volume',domain=domain('interval',[0,1]),scale_kind='predicate',polarity='supports',probability_model_ref=None)],
                missing_refs=['fact:anchor.visible'],derived_from=['e:rule:1'],error_code=None)
decision=dict(id='decision:pin:1',author='human',state='accepted',type='pin',target_refs=['owned:trousers','p:lower'],
              scope='outfit:1',reason_ref='e:user:1',revision=1)
outfit=dict(id='outfit:1',revision='1',scene_ids=['scene:gallery'],
            placements=[dict(id='p:top',item_ref='variant:top',part_ref=None,roles=['upper'],covers=['torso'],wear_state_ref='fact:wear:top'),
                        dict(id='p:lower',item_ref='owned:trousers',part_ref=None,roles=['lower'],covers=['legs'],wear_state_ref='fact:wear:lower')],
            membership_revision=1,decision_ids=[decision['id']])
sample=dict(schema_version='lyusterko.interaction/0.1-proposal',synthetic=True,nodes=nodes,evidence=evidence,facts=facts,
            factors=[factor],evaluations=[evaluation],decisions=[decision],outfits=[outfit])
jsonschema.Draft202012Validator.check_schema(schema)
jsonschema.validate(sample,schema)
node_ids={n['id'] for n in nodes}; fact_ids={f['id'] for f in facts}; evidence_ids={e['id'] for e in evidence}
assert len(node_ids)==len(nodes) and len(fact_ids)==len(facts)
assert all(f['subject'] in node_ids and set(f['evidence_ids'])<=evidence_ids for f in facts)
assert all(set(b['node_ids'])<=node_ids for b in factor['bindings'])
assert all(p['item_ref'] in node_ids and p['wear_state_ref'] in fact_ids for p in outfit['placements'])
assert set(factor['read_set']+factor['guard_read_set'])<=fact_ids
assert all(v['ref'] in fact_ids|{'outfit:1.membership'} for v in evaluation['input_versions'])
for name,value in [('contracts.schema.json',schema),('example_graph.json',sample)]:
    (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print('JSON Schema syntax, synthetic sample and six referential assertions: valid. Full domain and protocol semantics remain as described in the report; this is a core subgraph, not a complete wardrobe protocol.')
