# Independent kernel program author, deliberately never reads adapter requests.
import json,hashlib
from pathlib import Path
out=Path('test/fixtures/presumption-authoring')
span={'start':0,'end':1,'start_line':1,'start_col':1,'end_line':1,'end_col':2}
text='x'
def condition(leaf): return {'kind':'leaf_effective','leaf_id':leaf,'span':span}
def request(t='proved',r='not_proved',k='not_proved',chain=False,multiple=False,guard=False,group=False):
    statuses={'T':t,'R':r,'K':k}
    if chain: statuses['P']='not_proved'
    if guard: statuses['main']='unresolved'
    def rule(name,leaf,exceptions=[]):
        req={'id':leaf,'kind':'leaf','path':[name+'-branch'],'span':span}
        if group and name=='rule:selected':
            req={'id':'group','kind':'all','path':[name+'-branch'],'span':span,'members':[req,{'id':'extra','kind':'leaf','path':[name+'-branch'],'span':span}]}
        return {'id':name,'source_id':'source:reference','program':{'id':name+'-branch','path':[name+'-branch'],'span':span,'definitions':False,'children':[],'penalties':[],'requirements':[req]},'exceptions':exceptions}
    rules=[rule('rule:selected','main' if guard else 'K',[{'id':'exception:reference','branch_id':'rule:selected-branch','source_id':'source:reference','span':span,'effect':'defeat','guard':{'kind':'is_infringed','target':'rule:guard'}}] if guard else [])]
    if guard: rules.append(rule('rule:guard','K'))
    rules.extend(rule('storage:'+x,x) for x in statuses if x not in ['K','main'])
    if group:statuses['extra']='proved'
    facts={key:{'proof_status':{'kind':value,**({'reason':'not_determined'} if value=='unresolved' else {})},'status_source':{'assignment_id':'assignment:'+key,'issuer_label':'Independent reference fixture','origin':'synthetic_fixture','source_id':'source:reference','span':span}} for key,value in statuses.items()}
    def reg(id,target,trigger):return {'presumption_id':id,'target_leaf_id':target,'source_id':'source:reference','span':span,'trigger':condition(trigger),'rebuttal':condition('R')}
    regs=[reg('registration:knowledge','K','P' if chain else 'T')]
    if chain:regs.insert(0,reg('registration:possession','P','T'))
    if multiple:regs.append(reg('registration:alternative','K','T'))
    return {'protocol':'yuho.kernel-protocol/v1','request_id':'R01','operation':'evaluate','input_schema':'yuho.kernel-input/v1','fragment':'RegisteredPresumptionDerivations-v1','sources':[{'id':'source:reference','path':'independent/synthetic.txt','text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}],'policy':{'max_nodes':1024,'reference_date':'2021-12-31'},'registry':rules,'root_rule':'rule:selected','facts':facts,'presumptions':regs}
cases={'P1-active':request(),'P2-rebutted':request(r='proved'),'P3-direct-dominance':request(r='proved',k='proved'),'P4-inactive':request(t='not_proved',r='unresolved'),'P5-unresolved':request(t='unresolved'),'P6-multiple':request(multiple=True),'P7-skipped-guard':request(guard=True),'chain-active':request(chain=True),'chain-rebutted':request(chain=True,r='proved'),'chain-uncertain':request(chain=True,t='unresolved'),'chain-direct':request(chain=True,r='proved',k='proved'),'group':request(group=True)}
cases['guard-defeat']=request(guard=True);cases['guard-defeat']['facts']['main']['proof_status']={'kind':'proved'}
cases['guard-unresolved']=request(guard=True,t='unresolved');cases['guard-unresolved']['facts']['main']['proof_status']={'kind':'proved'}
for name,value in cases.items():(out/(name+'.reference.json')).write_text(json.dumps(value,indent=2)+'\n')
