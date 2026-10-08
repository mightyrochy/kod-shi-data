"""Independent research prototype, synthetic data; no product imports or IO.

Not a stylist and not a complete proposed engine. Exact interval arithmetic,
dependency invalidation, scoped human decisions, stable identity and a bounded
synthetic performance workload are exercised independently of product code.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from hashlib import sha256
from itertools import product, combinations
import json
import math
import statistics
import time


@dataclass(frozen=True)
class Interval:
    lo: F
    hi: F

    def __init__(self, lo, hi=None):
        object.__setattr__(self, 'lo', F(str(lo)))
        object.__setattr__(self, 'hi', F(str(lo if hi is None else hi)))
        if self.lo > self.hi:
            raise ValueError('Empty/conflicting interval is not an unknown value')

    def __add__(self, other):
        return Interval(self.lo+other.lo, self.hi+other.hi)

    def __sub__(self, other):
        return Interval(self.lo-other.hi, self.hi-other.lo)

    def as_list(self):
        return [float(self.lo), float(self.hi)]


def robust_at_least(x, threshold):
    if x is None:
        return 'unknown'
    if x.lo >= threshold:
        return 'satisfied'
    if x.hi < threshold:
        return 'violated'
    return 'indeterminate'


def volume(top, bottom, anchor, waist_goal=True):
    """An explicit STYLISTIC HYPOTHESIS, never a physical law or beauty score."""
    if not waist_goal:
        return {'applicability':'false', 'status':'not_applicable'}
    possibilities = [v if v is not None else (0,1) for v in (top,bottom,anchor)]
    rows = list(product(*possibilities))
    concern = [a*b*(1-c) for a,b,c in rows]
    support = [a*b*c for a,b,c in rows]
    return {'applicability':'true',
            'status':'unknown' if any(v is None for v in (top,bottom,anchor)) else 'evaluated',
            'concern':[min(concern),max(concern)], 'support':[min(support),max(support)],
            'kind':'uncalibrated_stylistic_predicate', 'probability':None}


def stable_factor_id(rule, role_bindings, scope):
    # Roles are retained; a symmetric set role must sort its own members.
    raw = json.dumps([rule,sorted(role_bindings.items()),scope],sort_keys=True,separators=(',',':'))
    return sha256(raw.encode()).hexdigest()[:24]


class Engine:
    """Small DAG. Declared guard/missing dependencies remain indexed always."""
    def __init__(self):
        self.facts = {}
        self.rules = {}
        self.reverse = {}
        self.cache = {}
        self.calls = {}

    def add(self, key, dependencies, evaluate):
        self.rules[key] = (tuple(dependencies), evaluate)
        for dep in dependencies:
            self.reverse.setdefault(dep,set()).add(key)

    def put(self, key, value):
        oldrev = self.facts.get(key,(None,0))[1]
        self.facts[key] = (value,oldrev+1)
        todo = list(self.reverse.get(key,()))
        dirty = set()
        while todo:
            k = todo.pop()
            if k in dirty:
                continue
            dirty.add(k)
            self.cache.pop(k,None)
            todo.extend(self.reverse.get('@'+k,()))
        return sorted(dirty)

    def get(self, key):
        if key.startswith('@'):
            return self.evaluate(key[1:])
        return self.facts.get(key,(None,0))[0]

    def evaluate(self, key, active=None):
        if key in self.cache:
            return self.cache[key]
        active = set() if active is None else active
        if key in active:
            raise ValueError('Derivation cycle')
        active.add(key)
        deps,fn = self.rules[key]
        values = [self.evaluate(d[1:],active) if d.startswith('@') else self.get(d) for d in deps]
        active.remove(key)
        answer = fn(*values)
        self.cache[key] = answer
        self.calls[key] = self.calls.get(key,0)+1
        return answer


def replace_placement(placements, placement, new_item, pins):
    if placement in pins and pins[placement] != new_item:
        return {'status':'pin_conflict','placements':dict(placements)}
    return {'status':'changed','placements':dict(placements,**{placement:new_item})}


def policy_disposition(measurement, decision, rule, participants, scope):
    # A decision affects how to act, never changes the observation.
    allowed = (decision.get('author')=='human' and decision.get('state')=='accepted'
               and decision.get('rule')==rule and set(decision.get('participants',()))==set(participants)
               and decision.get('scope')==scope)
    return {'measurement':measurement,'disposition':'accepted_deviation' if allowed else 'open'}


def robust_dominates(a,b):
    """All dimensions MINIMIZED and separately meaningful. Missing => incomparable."""
    if any(v is None for v in a+b):
        return False
    return all(x.hi<=y.lo for x,y in zip(a,b)) and any(x.hi<y.lo for x,y in zip(a,b))


def checks_and_examples():
    passed=[]
    def check(name,condition):
        if not condition: raise AssertionError(name)
        passed.append(name)
    unknown = volume((1,),(1,),None)
    opened = volume((1,),(1,),(1,))
    closed = volume((1,),(1,),(0,))
    check('missing_anchor_not_success',unknown['status']=='unknown' and unknown['concern']==[0,1])
    check('positive_support_explicit',opened['support']==[1,1] and opened['concern']==[0,0])
    check('closed_layer_changes_multiway_result',closed['concern']==[1,1])
    check('goal_change_not_body_change',volume((1,),(1,),(0,),False)['status']=='not_applicable')
    check('symmetric_role_permutation',volume((0,1),(1,),(1,))==volume((1,),(0,1),(1,)))
    a=stable_factor_id('r@1',{'upper':'p1','lower':'p2'},'s1')
    b=stable_factor_id('r@1',{'lower':'p2','upper':'p1'},'s1')
    check('id_independent_of_enumeration_order',a==b)
    check('role_swap_changes_identity',a!=stable_factor_id('r@1',{'upper':'p2','lower':'p1'},'s1'))
    eng=Engine()
    eng.add('volume',('top','bottom','anchor','goal'),volume)
    eng.add('explanation',('@volume',),lambda r: ('uses',r))
    eng.add('colour',('hue',),lambda h: h)
    for k,v in {'top':(1,),'bottom':(1,),'goal':True,'hue':(10,20)}.items(): eng.put(k,v)
    eng.evaluate('explanation'); eng.evaluate('colour')
    invalidated=eng.put('anchor',(1,))
    check('missing_field_later_invalidates',set(invalidated)=={'volume','explanation'})
    check('incremental_matches_fresh',eng.evaluate('volume')==opened)
    eng.evaluate('explanation'); eng.evaluate('colour')
    check('unrelated_colour_cache_preserved',eng.calls['colour']==1)
    eng.put('goal',False); eng.evaluate('explanation')
    eng.put('goal',True)
    check('inapplicable_guard_is_dependency',eng.evaluate('volume')==opened)
    eng.add('all_items',('membership',),lambda items: len(items or []))
    eng.put('membership',['p1']); eng.evaluate('all_items')
    eng.put('membership',['p1','p2'])
    check('new_member_invalidates_quantifier',eng.evaluate('all_items')==2)
    pin=replace_placement({'lower':'owned:1'},'lower','catalog:2',{'lower':'owned:1'})
    check('locked_owned_item_preserved',pin['status']=='pin_conflict' and pin['placements']['lower']=='owned:1')
    decision=dict(author='human',state='accepted',rule='register',participants=['p1','p2'],scope='gallery')
    disposition=policy_disposition({'register_gap':'present'},decision,'register',['p1','p2'],'gallery')
    check('accepted_break_does_not_erase_measurement',disposition['measurement']['register_gap']=='present')
    check('decision_does_not_leak_context',policy_disposition(1,decision,'register',['p1','p2'],'office')['disposition']=='open')
    check('model_proposal_not_human_consent',policy_disposition(1,dict(decision,author='stylist'), 'register',['p1','p2'],'gallery')['disposition']=='open')
    hem=Interval(1,3); gait=Interval(2,4)
    old=hem+Interval(1,2)-gait
    new=hem+Interval(4,5)-gait
    check('hem_interval_exact',old.as_list()==[-2.0,3.0] and new.as_list()==[1.0,6.0])
    check('uncertainty_widening_cannot_prove_threshold',robust_at_least(Interval(-1,6),1)=='indeterminate')
    check('unknown_hem_remains_unknown',robust_at_least(None,1)=='unknown')
    check('threshold_boundary_inclusive',robust_at_least(new,1)=='satisfied')
    waist=Interval(84,86)-Interval(78,82)
    check('person_domain_used_not_body_type',waist.as_list()==[2.0,8.0])
    # A single shared latent q: q+(1-q) is exactly 1, not independent [0,2].
    shared=[q+(1-q) for q in (0,1)]
    check('shared_latent_constraints_preserved',min(shared)==max(shared)==1)
    check('pareto_incomparability',not robust_dominates([Interval(0),Interval(2)],[Interval(1),Interval(1)]))
    check('unknown_not_zero_cost',not robust_dominates([Interval(0),None],[Interval(1),Interval(1)]))
    check('strict_robust_dominance',robust_dominates([Interval(0),Interval(1)],[Interval(1),Interval(2)]))
    bad=Engine(); bad.add('a',('@b',),lambda x:x); bad.add('b',('@a',),lambda x:x)
    try: bad.evaluate('a'); cycle=False
    except ValueError: cycle=True
    check('cyclic_derivation_rejected',cycle)
    rows=[]
    for x,y,z in product((0,1),repeat=3):
        exact=x*y*(1-z)
        pair=0.5*x*y-0.5*x*z-0.5*y*z+0.25*(x+y+z)-0.125
        rows.append({'a':x,'b':y,'c':z,'factor':exact,'best_additive_pairwise':pair,'residual':exact-pair})
    third=sum((-1)**(3-r['a']-r['b']-r['c'])*r['factor'] for r in rows)
    rmse=math.sqrt(sum(r['residual']**2 for r in rows)/8)
    check('nonzero_third_mixed_difference',third==-1 and rmse==0.125)
    return {'synthetic':True,'checks_passed':passed,'check_count':len(passed),
            'volume':{'unknown':unknown,'open':opened,'closed':closed,'waist_reserve_cm':waist.as_list()},
            'deliberate_break':disposition,
            'clearance':{'old_cm':old.as_list(),'new_cm':new.as_list(),'new_status':robust_at_least(new,1)},
            'invalidation':invalidated,'pairwise_counterexample':{'rows':rows,'third_difference':third,'rmse':rmse}}


def benchmark():
    """Synthetic indexing workload; timings do not predict end-to-end UX."""
    pool={f'p:{s}:{i}':(i%2,(i+s)%7) for s in range(17) for i in range(25)}
    eng=Engine(); n=8
    for s in range(n): eng.put(f'slot:{s}',pool[f'p:{s}:0'])
    for s in range(n): eng.add(f'unary:{s}',(f'slot:{s}',),lambda a:a[1])
    for a,b in combinations(range(n),2):
        eng.add(f'pair:{a}:{b}',(f'slot:{a}',f'slot:{b}'),lambda a,b:abs(a[1]-b[1]))
    for a in range(n):
        eng.add(f'triple:{a}',tuple(f'slot:{i%n}' for i in (a,a+1,a+2)),lambda a,b,c:a[0]*b[0]*(1-c[0]))
    eng.add('global:sum',tuple(f'slot:{i}' for i in range(n)),lambda *items:sum(a[1] for a in items))
    eng.add('global:max',tuple(f'slot:{i}' for i in range(n)),lambda *items:max(a[1] for a in items))
    keys=list(eng.rules)
    for k in keys: eng.evaluate(k)
    full=[]; local=[]; dirty_sizes=[]
    for i in range(200):
        s=i%n; item=pool[f'p:{s}:{(i+1)%25}']
        start=time.perf_counter(); dirty=eng.put(f'slot:{s}',item)
        for k in keys: eng.evaluate(k)
        local.append((time.perf_counter()-start)*1000); dirty_sizes.append(len(dirty))
        current=dict(eng.cache)
        start=time.perf_counter(); eng.cache.clear()
        for k in keys: eng.evaluate(k)
        full.append((time.perf_counter()-start)*1000)
        if current!=eng.cache: raise AssertionError('Incremental differs from complete recomputation')
    quant=lambda xs: {'p50_ms':round(statistics.median(xs),6),'p95_ms':round(sorted(xs)[math.ceil(.95*len(xs))-1],6)}
    return {'synthetic':True,'pool_items':len(pool),'pool_slots':17,'outfit_items':n,
            'factors':len(keys),'candidates_checked':200,'dirty_factors':sorted(set(dirty_sizes)),
            'incremental':quant(local),'full':quant(full),'incremental_equals_full':True,
            'json_pool_bytes':len(json.dumps(pool).encode()),
            'disclaimer':'Toy evaluators only; excludes input extraction, templates, actual style rules, browser UI and model calls.'}


def run():
    return {'examples_and_invariants':checks_and_examples(),'benchmark':benchmark()}


if __name__=='__main__':
    print(json.dumps(run(),ensure_ascii=False,indent=2))
