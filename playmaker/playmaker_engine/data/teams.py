# Prescribed teams. Rules: one card per position; tier shape BBBBB, ABBBC or AABCC (equal A and C);
# every team covers four jobs (a creator, two shooters, a rim anchor, a point-of-attack stopper),
# except where the identity trades exactly one away; strengths within a tight band; no card used twice.
TEAMS = [
 ('Pace and Space',    'Four shooters spread it; a rim runner dives into the gap.', ['cgB','tndB','stsfB','pnpB','rrcB']),
 ('Iron Wall',         'Three stoppers and a rim protector, plus a scorer.', ['dpgB','bgsB','dfsfB','stpfB','rpcB']),
 ('Twin Towers',       'Two post scorers inside, a scoring wing and a stopper outside.', ['spgC','twA','scsfA','pspfC','pscB']),
 ('Run and Gun',       'Get out early: attack the rim before the defence is set.', ['apgB','twB','scsfB','dpfA','rrcC']),
 ('Ball Movement',     'Two passers feeding a shooter and two posts. Find the open man.', ['ppgA','shsC','pfsfB','arpfA','pscC']),
 ('Shoot and Protect', 'Elite three-and-D wings out front, a rim protector behind.', ['ppgB','tndA','stsfA','stpfC','rpcC']),
 ('Bucket Brigade',    'Pure scoring. No stopper on purpose: outscore them.', ['spgA','bgsC','scsfC','pspfA','pmcB']),
 ('Five Out',          'Everyone shoots the three, even the centre.', ['ppgC','shsA','twsfB','stpfA','stcC']),
 ('High-Low',          'A passing four up top feeds an elite post scorer below.', ['cgA','pmsC','stsfC','arpfB','pscA']),
 ('Lockdown',          'An elite two-way wing and a big who anchors the defence.', ['dpgC','tndC','twsfA','dpfB','pmcA']),
]
DROPS = {'Bucket Brigade': 'stopper'}
FIRST_GAME = ('Five Out', 'High-Low')
