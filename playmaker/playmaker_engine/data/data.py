# Player card data, transcribed from the printed cards (the cards are the source of truth).
# Values: number + band (H above average, A average, L below average).
# Offence: dribble, pass, screen | layup, dunk, post, floater, mid, long2, three, free throw
# Defence: agility, intercept, challenge, steal, foul(steal) | layup, dunk, post, floater, mid, long2, three, foul(contest)
# qs: Quick Step from the speed colour (green 2, yellow 1, red 0)
CARDS = [
 # key, piece no, role, tier, tagline, qs, offence, defence
 ('apgA',1,'Attacking Point Guard','A','Explosive athlete. Elite finisher. Average shooter.',2,
  '19H 15A 14A | 19H 18H 11L 15H 11H 9A 9A 14A', '8H 8H 8H 4H 7A | 7A 3A 4A 4A 3H 2A 2A 9A'),
 ('apgB',1,'Attacking Point Guard','B','Quick athlete. Strong finisher. Unreliable shooter.',2,
  '17H 14A 12L | 19H 17A 10L 14H 10A 9A 9A 13L', '7A 7A 7A 3A 8A | 6L 2L 3L 3A 2A 2A 2A 10L'),
 ('apgC',1,'Attacking Point Guard','C','Decent attacker, limited shooter. Foul prone.',1,
  '16A 13L 11L | 18A 16A 9L 13H 10A 8A 8A 12L', '6A 7A 6A 3A 9L | 5L 1L 2L 2L 2A 1L 1L 11L'),
 ('cgA',1,'Combo Guard','A','Well-rounded. Above-average in most skills.',2,
  '17H 18H 15A | 18A 17A 11L 12A 11H 10H 9A 16A', '8H 8H 8H 3A 6H | 8A 3A 4A 4A 3H 3H 2A 10L'),
 ('cgB',1,'Combo Guard','B','Versatile skills. Above-average playmaking.',1,
  '15A 17H 13L | 18A 16A 10L 11A 10A 9A 9A 15A', '7A 7A 7A 3A 7A | 7A 2L 3L 3A 3H 2A 2A 11L'),
 ('cgC',1,'Combo Guard','C','Serviceable playmaker. Liability on defence.',1,
  '15A 16A 11L | 17L 15L 9L 10A 10A 9A 9A 15A', '5L 6A 5L 2A 8A | 5L 1L 2L 2L 2A 2A 2A 12L'),
 ('dpgA',1,'Defensive Point Guard','A','Elite defender. Great athlete. Average offence.',2,
  '16A 15A 16A | 18A 16A 10L 9L 10A 8A 9A 15A', '10H 9H 10H 5H 4H | 9A 4A 5A 4A 4H 3H 3H 7H'),
 ('dpgB',1,'Defensive Point Guard','B','Strong, athletic defender. Below-average offence.',1,
  '16A 14A 14A | 17L 15L 9L 8L 9A 8A 8A 14A', '9H 8H 9H 5H 5H | 8A 3A 4A 3A 3H 3H 2A 8A'),
 ('dpgC',1,'Defensive Point Guard','C','Undersized but smart defender. Poor offensive skill.',2,
  '15A 13L 12L | 17L 15L 8L 8L 9A 7L 7L 13L', '8H 7A 8H 4H 6H | 6L 2L 3L 2L 3H 2A 2A 9A'),
 ('spgA',1,'Scoring Point Guard','A','Elite scorer and ball-handler. Average defence.',2,
  '19H 16A 14A | 19H 17A 12A 15H 12H 10H 10H 18H', '7A 7A 7A 3A 7A | 7A 3A 4A 3A 2A 2A 2A 9A'),
 ('spgB',1,'Scoring Point Guard','B','Confident scorer and ball-handler. Poor defender.',1,
  '18H 15A 12L | 18A 16A 11L 14H 11H 10H 9A 17H', '6A 6A 6A 3A 8A | 6L 2L 3L 2L 2A 2A 2A 10L'),
 ('spgC',1,'Scoring Point Guard','C','Solid scorer. Good handles. Weak defence. Foul prone.',1,
  '17H 14A 11L | 18A 15L 10L 13H 11H 9A 9A 16A', '5L 6A 5L 2A 9L | 5L 1L 2L 2L 2A 2A 2A 11L'),
 ('ppgA',1,'Pass-First Point Guard','A','Elite playmaker. Strong handles. Average scoring.',2,
  '19H 20H 15A | 18A 16A 10L 11A 11H 9A 9A 15A', '8H 7A 8H 3A 6H | 8A 3A 4A 3A 3H 2A 2A 9A'),
 ('ppgB',1,'Pass-First Point Guard','B','Good playmaker. Solid handles. Limited scoring.',1,
  '18H 19H 13L | 17L 15L 9L 10A 10A 8A 9A 14A', '7A 6A 7A 3A 7A | 7A 2L 3L 2L 2A 2A 2A 10L'),
 ('ppgC',1,'Pass-First Point Guard','C','Decent playmaker. Good handles. Poor scorer.',1,
  '17H 18H 11L | 17L 15L 9L 9L 10A 8A 8A 13L', '6A 5L 6A 3A 8A | 6L 1L 2L 2L 2A 2A 2A 11L'),
 ('twA',2,'Two-Way Shooting Guard','A','Strong defender and scorer. Well-rounded skills.',1,
  '15A 15A 16A | 18A 17A 12A 11A 11H 10H 9A 16A', '9H 9H 9H 5H 5H | 9A 4A 5A 4A 4H 3H 3H 7H'),
 ('twB',2,'Two-Way Shooting Guard','B','Solid defender and scorer. Balanced skills.',1,
  '14A 15A 14A | 18A 16A 11L 10A 11H 9A 9A 15A', '8H 8H 8H 4H 6H | 8A 3A 4A 3A 3H 3H 2A 8A'),
 ('twC',2,'Two-Way Shooting Guard','C','Jack-of-all-trades. No standout skills.',1,
  '14A 13L 12L | 17L 15L 10L 9L 10A 9A 9A 15A', '7A 7A 7A 4H 7A | 6L 2L 3L 2L 3H 2A 2A 9A'),
 ('tndA',2,'Three-and-D Shooting Guard','A','Elite defender. Excellent shooter. Limited playmaking.',1,
  '14A 13L 15A | 18A 16A 11L 9L 12H 10H 10H 17H', '9H 8H 9H 5H 5H | 9A 4A 5A 4A 4H 4H 3H 7H'),
 ('tndB',2,'Three-and-D Shooting Guard','B','Good defender and shooter. Limited playmaking.',1,
  '13L 12L 13L | 17L 15L 10L 8L 11H 10H 9A 17H', '8H 8H 8H 4H 6H | 8A 3A 4A 3A 4H 3H 3H 8A'),
 ('tndC',2,'Three-and-D Shooting Guard','C','Decent at shooting and defending shooters.',1,
  '12L 11L 11L | 17L 15L 9L 8L 11H 9A 9A 16A', '7A 7A 7A 3A 7A | 6L 2L 3L 2L 3H 3H 2A 9A'),
 ('pmsA',2,'Playmaker Shooting Guard','A','Elite playmaker. Decent scorer. Average defender.',1,
  '18H 18H 15A | 18A 16A 12A 13H 11H 9A 9A 16A', '7A 7A 7A 3A 6H | 8A 3A 4A 4A 3H 2A 2A 10L'),
 ('pmsB',2,'Playmaker Shooting Guard','B','Strong playmaker. Average scorer.',1,
  '17H 17H 13L | 18A 15L 11L 11A 10A 9A 9A 15A', '6A 6A 6A 3A 7A | 7A 2L 3L 3A 2A 2A 2A 11L'),
 ('pmsC',2,'Playmaker Shooting Guard','C','Solid playmaker. Poor defender. Foul prone.',1,
  '16A 16A 11L | 17L 15L 10L 11A 10A 8A 8A 14A', '5L 6A 5L 2A 8A | 5L 1L 2L 2L 2A 2A 2A 12L'),
 ('shsA',2,'Sharpshooter Shooting Guard','A','Elite spot-up shooter. Average defender.',1,
  '15A 14A 14A | 18A 16A 11L 12A 12H 11H 11H 18H', '7A 6A 7A 2A 7A | 8A 3A 4A 3A 2A 2A 2A 9A'),
 ('shsB',2,'Sharpshooter Shooting Guard','B','Spot-up shooter. Poor playmaking. Weak defence.',1,
  '14A 13L 12L | 17L 15L 10L 11A 12H 10H 10H 17H', '6A 6A 6A 2A 8A | 7A 2L 3L 2L 2A 2A 2A 10L'),
 ('shsC',2,'Sharpshooter Shooting Guard','C','Decent spot-up shooter. Liability on defence.',1,
  '13L 12L 11L | 17L 15L 9L 10A 11H 10H 9A 16A', '5L 5L 5L 1L 9L | 5L 1L 2L 2L 2A 2A 2A 11L'),
 ('bgsA',2,'Bucket Getter Shooting Guard','A','Elite scorer. Average defender. Foul prone.',2,
  '18H 13L 14A | 19H 18H 13A 15H 12H 10H 10H 18H', '7A 7A 6A 2A 8A | 7A 3A 4A 3A 2A 2A 2A 11L'),
 ('bgsB',2,'Bucket Getter Shooting Guard','B','Strong scorer. Weak defender. Foul prone.',1,
  '17H 12L 12L | 19H 17A 12A 14H 11H 10H 9A 17H', '6A 7A 5L 2A 9L | 6L 2L 3L 2L 2A 2A 2A 12L'),
 ('bgsC',2,'Bucket Getter Shooting Guard','C','Good attacker. Poor defender. Foul prone.',1,
  '17H 11L 11L | 18A 16A 11L 13H 11H 9A 9A 16A', '5L 6A 4L 2A 10L | 5L 1L 2L 2L 2A 2A 2A 12L'),
 ('dpfA',4,'Defensive Power Forward','A','Elite defender. Athletic finisher. Poor shooter.',1,
  '14A 12L 17H | 18A 18H 15H 8L 9A 8A 7L 15A', '8H 9H 9H 4H 6H | 10H 6H 7H 4A 4H 4H 3H 5H'),
 ('dpfB',4,'Defensive Power Forward','B','Good defender. Solid finisher. Poor shooter.',0,
  '12L 11L 16A | 18A 17A 14A 8L 9A 7L 6L 14A', '7A 8H 8H 4H 7A | 10H 5H 6H 3A 4H 4H 3H 6H'),
 ('dpfC',4,'Defensive Power Forward','C','Serviceable defender. Liability on offence.',0,
  '11L 11L 15A | 17L 16A 13A 8L 9A 7L 6L 12L', '6A 7A 7A 3A 8A | 8A 4A 5A 2L 3H 3H 2A 7H'),
 ('arpfA',4,'All-Rounder Power Forward','A','Versatile scorer. Solid defender.',1,
  '15A 15A 18H | 19H 18H 16H 9L 11H 9A 9A 15A', '7A 7A 8H 3A 7A | 10H 5H 6H 4A 3H 3H 2A 7H'),
 ('arpfB',4,'All-Rounder Power Forward','B','Balanced scorer. Average defender.',1,
  '13L 14A 17H | 18A 17A 15H 8L 10A 9A 8A 14A', '6A 6A 7A 3A 8A | 9A 4A 5A 3A 3H 3H 2A 8A'),
 ('arpfC',4,'All-Rounder Power Forward','C','Decent screener. No other standout skills.',0,
  '12L 13L 16A | 17L 16A 14A 8L 10A 8A 7L 12L', '5L 5L 6A 2A 9L | 7A 4A 4A 2L 2A 2A 2A 9A'),
 ('pnpA',4,'Pick-and-Pop Power Forward','A','Elite screener. Good shooter. Foul-prone defender.',1,
  '16A 14A 19H | 18A 18H 15H 9L 11H 10H 9A 16A', '6A 7A 7A 2A 8A | 9A 5H 5A 4A 3H 3H 2A 9A'),
 ('pnpB',4,'Pick-and-Pop Power Forward','B','Strong screener. Average shooter. Poor defender.',0,
  '15A 13L 18H | 18A 17A 14A 8L 11H 9A 9A 15A', '5L 6A 6A 2A 9L | 8A 4A 4A 3A 2A 2A 2A 10L'),
 ('pnpC',4,'Pick-and-Pop Power Forward','C','Good screener. Average shooter. Poor defender.',0,
  '14A 12L 17H | 17L 16A 13A 8L 10A 9A 8A 14A', '4L 5L 5L 2A 10L | 6L 3A 3L 2L 2A 2A 2A 11L'),
 # stpfA defence: card printed colours but no numbers; values are tier B + 1 (provisional, awaiting confirmation)
 ('stpfA',4,'Stretch Power Forward','A','Strong shooter. Average, foul-prone defender.',1,
  '14A 14A 16A | 18A 17A 14A 10A 12H 10H 9A 18H', '6A 7A 7A 3A 8A | 9A 5H 5A 4A 3H 3H 2A 9A'),
 ('stpfB',4,'Stretch Power Forward','B','Good shooter. Below-average defender.',0,
  '12L 13L 15A | 17L 16A 13A 9L 11H 10H 9A 16A', '5L 6A 6A 2A 9L | 8A 4A 4A 3A 2A 2A 2A 10L'),
 ('stpfC',4,'Stretch Power Forward','C','Average shooter. Poor defender.',0,
  '11L 12L 14A | 17L 15L 12A 8L 11H 9A 9A 14A', '4L 5L 5L 2A 10L | 6L 3A 3L 2L 2A 2A 2A 11L'),
 ('pspfA',4,'Post Scorer Power Forward','A','Dominant inside scorer. Slow, imposing defender.',0,
  '14A 13L 18H | 19H 19H 17H 9L 10A 8A 7L 15A', '6A 6A 6A 2A 9L | 10H 5H 6H 4A 3H 3H 2A 8A'),
 ('pspfB',4,'Post Scorer Power Forward','B','Strong inside scorer and screener. Slow defender.',0,
  '12L 13L 17H | 19H 18H 16H 8L 10A 8A 6L 13L', '5L 6A 5L 2A 10L | 9A 4A 5A 3A 3H 3H 2A 9A'),
 ('pspfC',4,'Post Scorer Power Forward','C','Decent inside scorer. Poor shooter and defender.',0,
  '11L 13L 16A | 18A 17A 15H 8L 9A 7L 6L 12L', '4L 5L 4L 1L 11L | 7A 4A 4A 2L 2A 2A 2A 10L'),
 ('rpcA',5,'Rim Protector Centre','A','Elite defender. Strong post moves. Poor shooter.',0,
  '12L 12L 18H | 18A 18H 16H 8L 9A 7L 6L 12L', '7A 9H 8H 3A 7A | 10H 6H 8H 5H 4H 4H 3H 4H'),
 ('rpcB',5,'Rim Protector Centre','B','Strong defender. Good post moves. Poor shooter.',0,
  '11L 12L 17H | 18A 17A 15H 8L 9A 7L 6L 12L', '6A 8H 7A 2A 8A | 10H 5H 7H 5H 4H 4H 2A 5H'),
 ('rpcC',5,'Rim Protector Centre','C','Decent defender. Limited offence. Poor shooter.',0,
  '11L 11L 16A | 17L 16A 14A 8L 9A 7L 5L 10L', '5L 7A 6A 2A 9L | 9A 5H 6H 4A 3H 3H 2A 6H'),
 ('stcA',5,'Stretch Centre','A','Good shooter. Versatile skill set. Average defender.',1,
  '15A 14A 16A | 18A 17A 15H 9L 12H 10H 9A 15A', '6A 6A 7A 3A 8A | 10H 5H 6H 5H 3H 3H 2A 7H'),
 ('stcB',5,'Stretch Centre','B','Decent shooter. Average defender with poor footwork.',0,
  '14A 13L 15A | 17L 16A 14A 8L 11H 9A 9A 14A', '5L 6A 6A 3A 9L | 9A 4A 5A 4A 3H 3H 2A 8A'),
 ('stcC',5,'Stretch Centre','C','Average shooter. Poor defender. Limited athleticism.',0,
  '13L 12L 14A | 17L 15L 13A 8L 11H 9A 8A 14A', '4L 5L 5L 2A 10L | 7A 4A 4A 3A 2A 2A 2A 9A'),
 ('pmcA',5,'Playmaking Centre','A','Great passer and screener with a versatile skill set.',0,
  '16A 17H 17H | 18A 18H 16H 11A 11H 9A 8A 17H', '6A 7A 7A 4H 7A | 10H 5H 6H 4A 3H 3H 2A 8A'),
 ('pmcB',5,'Playmaking Centre','B','Good passer and screener. Struggles defending guards.',0,
  '14A 16A 16A | 18A 17A 15H 10A 10A 8A 7L 15A', '5L 6A 6A 2A 8A | 9A 4A 5A 4A 2A 2A 2A 9A'),
 ('pmcC',5,'Playmaking Centre','C','Good passer. Poor defender.',0,
  '14A 15A 15A | 17L 16A 14A 9L 10A 8A 6L 13L', '4L 5L 5L 2A 9L | 7A 4A 4A 3A 2A 2A 2A 10L'),
 ('pscA',5,'Post Scorer Centre','A','Elite inside scorer. Shot blocker. Poor perimeter skills.',0,
  '14A 13L 19H | 19H 19H 18H 9L 10A 8A 6L 14A', '5L 6A 5L 2A 9L | 10H 6H 7H 4A 3H 3H 2A 6H'),
 ('pscB',5,'Post Scorer Centre','B','Strong inside scorer and screener. Poor perimeter skills.',0,
  '13L 12L 18H | 19H 18H 17H 8L 9A 7L 6L 13L', '4L 6A 4L 2A 10L | 10H 5H 6H 3A 3H 3H 2A 7H'),
 ('pscC',5,'Post Scorer Centre','C','Inside scorer. Poor defender. Lacks perimeter skills.',0,
  '12L 11L 17H | 18A 17A 16H 8L 9A 7L 6L 11L', '3L 5L 4L 1L 11L | 8A 4A 5A 3A 2A 2A 2A 8A'),
 ('rrcA',5,'Rim Runner Centre','A','Elite, athletic finisher. Strong defender. Poor shooter.',1,
  '12L 12L 18H | 19H 19H 16H 9L 9A 8A 6L 12L', '7A 8H 6A 4H 8A | 10H 6H 7H 5H 4H 4H 2A 5H'),
 ('rrcB',5,'Rim Runner Centre','B','Strong, fast finisher. Good athlete. Poor shooter.',1,
  '11L 11L 17H | 19H 19H 15H 8L 9A 7L 6L 11L', '6A 7A 5L 3A 9L | 10H 5H 6H 4A 3H 3H 2A 6H'),
 ('rrcC',5,'Rim Runner Centre','C','Decent finisher. Average defender. Limited skill set.',1,
  '11L 11L 16A | 18A 17A 14A 8L 9A 7L 5L 10L', '5L 6A 4L 2A 10L | 8A 4A 5A 3A 3H 3H 2A 7H'),
 ('twsfA',3,'Two-Way Small Forward','A','Great defender and scorer. Versatile player.',1,
  '16A 15A 17H | 18A 17A 14A 11A 11H 9A 9A 16A', '9H 9H 9H 4H 6H | 10H 5H 6H 4A 4H 4H 3H 8A'),
 ('twsfB',3,'Two-Way Small Forward','B','Good defender. Well-rounded skills. Solid athlete.',1,
  '15A 14A 15A | 18A 16A 13A 10A 10A 9A 9A 15A', '8H 8H 8H 3A 7A | 9A 4A 5A 3A 3H 3H 2A 9A'),
 ('stsfA',3,'Stretch Small Forward','A','Excellent shooter. Serviceable all-round skills.',1,
  '15A 14A 15A | 18A 16A 13A 11A 11H 10H 10H 17H', '7A 6A 7A 3A 7A | 9A 4A 5A 4A 3H 3H 2A 9A'),
 ('stsfB',3,'Stretch Small Forward','B','Good shooter. Decent size. Average defender. Foul prone.',1,
  '15A 13L 13L | 17L 15L 12A 10A 11H 10H 9A 15A', '6A 6A 6A 2A 8A | 8A 3A 4A 3A 3H 3H 2A 10L'),
 ('dfsfA',3,'Defensive Small Forward','A','Elite defender. Great athlete. Limited on offence.',1,
  '14A 13L 17H | 18A 17A 13A 9L 10A 8A 8A 14A', '9H 9H 10H 5H 5H | 10H 5H 7H 4A 4H 4H 3H 6H'),
 ('dfsfB',3,'Defensive Small Forward','B','Strong defender. Good athlete. Poor offensive game.',1,
  '13L 12L 15A | 18A 16A 12A 8L 9A 8A 7L 14A', '8H 8H 9H 4H 6H | 9A 4A 6H 3A 4H 4H 3H 7H'),
 ('scsfA',3,'Scoring Small Forward','A','Elite, athletic scorer. Solid defender.',1,
  '18H 15A 15A | 19H 18H 15H 12A 12H 10H 9A 17H', '7A 7A 7A 3A 7A | 8A 4A 5A 4A 3H 3H 2A 9A'),
 ('scsfB',3,'Scoring Small Forward','B','Strong scorer. Good athlete. Average defender.',1,
  '17H 14A 13L | 19H 17A 14A 11A 11H 10H 9A 16A', '6A 7A 6A 2A 8A | 7A 3A 4A 3A 2A 2A 2A 10L'),
 ('pfsfA',3,'Point Forward Small Forward','A','Elite playmaker. Great athleticism. Strong scorer.',1,
  '18H 18H 17H | 18A 17A 15H 11A 11H 10H 9A 16A', '7A 7A 8H 3A 6H | 9A 4A 5A 4A 3H 3H 2A 10L'),
 ('pfsfB',3,'Point Forward Small Forward','B','Strong playmaker. Good size. Versatile scorer.',1,
  '16A 17H 15A | 18A 16A 14A 10A 10A 9A 9A 15A', '6A 7A 7A 2A 7A | 8A 3A 4A 3A 3H 3H 2A 11L'),
 # Small Forward tier C: never printed. Derived by cards/derive_sf_c.py (tier B minus the median B-to-C drop
 # across the other 20 archetypes, clamped to the printed range; tested at 85% exact on held-out archetypes).
 # Quick Step from speed: A-to-C speed drops 1 in total on every Centre archetype.
 ('twsfC',3,'Two-Way Small Forward','C','Decent defender and scorer. No standout skills.',1,
  '14A 13L 14A | 17L 15L 12A 10A 10A 8A 8A 14A', '7A 7A 7A 2A 8A | 7A 3A 4A 2L 3H 3H 2A 10L'),
 ('stsfC',3,'Stretch Small Forward','C','Decent shooter. Poor defender. Foul prone.',0,
  '14A 12L 12L | 17L 15L 11L 10A 10A 9A 9A 14A', '5L 5L 5L 1L 9L | 6L 3A 3L 2L 2A 2A 2A 11L'),
 ('dfsfC',3,'Defensive Small Forward','C','Solid defender. Poor offensive game.',1,
  '12L 11L 14A | 17L 15L 11L 8L 9A 7L 6L 13L', '7A 7A 8H 3A 7A | 7A 4A 5A 2L 3H 3H 2A 8A'),
 ('scsfC',3,'Scoring Small Forward','C','Decent scorer. Poor defender. Foul prone.',1,
  '16A 13L 12L | 18A 16A 13A 11A 11H 9A 9A 15A', '5L 6A 5L 1L 9L | 5L 3A 3L 2L 2A 2A 1L 11L'),
 ('pfsfC',3,'Point Forward Small Forward','C','Decent playmaker. Average scorer. Weak defender.',1,
  '15A 16A 14A | 17L 15L 13A 10A 10A 9A 8A 14A', '5L 6A 6A 1L 8A | 6L 3A 3L 2L 2A 2A 2A 12L'),
]
# D-184 (Shaun, 14 Nov 2026): two new types, the app only for now. The table plays the 25 types above.
APP_CARDS = [
 # key, piece no, role, tier, tagline, qs, offence, defence
 ('slsfA',3,'Slashing Wing Small Forward','A','Explosive slasher. Lives at the rim. Poor shooter.',2,
  '17H 14A 13L | 19H 19H 12A 11A 9A 8A 7L 16A', '9H 8H 8H 4H 7A | 8A 3A 4A 4A 3H 3H 2A 9A'),
 ('slsfB',3,'Slashing Wing Small Forward','B','Strong driver. Finishes through contact. Unreliable shooter.',2,
  '16A 13L 12L | 18A 19H 11L 10A 8L 7L 6L 15A', '8H 7A 7A 3A 8A | 7A 3A 4A 3A 3H 3H 2A 10L'),
 ('slsfC',3,'Slashing Wing Small Forward','C','Willing driver. Limited range.',1,
  '15A 12L 11L | 17L 18H 10L 9L 7L 7L 6L 14A', '7A 6A 6A 3A 9L | 6L 2L 3L 3A 2A 2A 2A 11L'),
 ('swcA',5,'Switch Centre','A','Elite switcher. Guards one to five. Rim runner.',2,
  '14A 13L 16A | 19H 19H 13A 9L 9A 7L 6L 14A', '9H 7A 8H 3A 6H | 8A 4A 6H 4A 3H 3H 3H 6H'),
 ('swcB',5,'Switch Centre','B','Mobile big. Holds up on switches. Limited range.',1,
  '13L 12L 15A | 18A 19H 12A 8L 8L 7L 5L 13L', '8H 6A 7A 3A 7A | 7A 3A 5A 4A 3H 3H 2A 7H'),
 ('swcC',5,'Switch Centre','C','Serviceable switcher. Finishes inside.',1,
  '12L 11L 14A | 17L 18H 11L 8L 7L 6L 5L 13L', '7A 5L 6A 2A 8A | 6L 3A 4A 3A 2A 2A 2A 8A'),
]
APP_ONLY = {row[0] for row in APP_CARDS}
TABLE_CARDS = list(CARDS)
CARDS = CARDS + APP_CARDS

OFF = ['dribble', 'pass', 'screen', 'shot_layup', 'shot_dunk', 'shot_post', 'shot_floater', 'shot_mid', 'shot_long', 'shot_three', 'free_throw']
DEF = ['agility', 'intercept', 'challenge', 'steal', 'foul_steal', 'con_layup', 'con_dunk', 'con_post', 'con_floater', 'con_mid', 'con_long', 'con_three', 'foul_contest']
def parse(s): return [(int(t[:-1]), t[-1]) for t in s.replace('|', ' ').split()]

# Ceiling: 19 on every rating except Pass (20 allowed: a pass only rolls when an intercept contests it, so it is never a sure thing).
# RANGE TABLE (locked 2 Nov 2026; jump shots, the open layup and the jump-shot and dunk contests rescaled by D-184, 14 Nov 2026). Each entry: (lowest average, lowest above average); below the first is below average.
# Every card colour is generated from this table. Layup ratings: 17->16 for the weakest finishers so finishing matters at the rim; top stays 19 (95%), no one is a sure thing.
RANGES = {'dribble': (14, 17), 'pass': (14, 17), 'screen': (14, 17), 'shot_layup': (18, 19), 'shot_dunk': (16, 18), 'shot_post': (12, 15), 'shot_floater': (10, 13), 'shot_mid': (9, 11), 'shot_long': (8, 10), 'shot_three': (8, 10), 'free_throw': (14, 17), 'agility': (6, 8), 'intercept': (6, 8), 'challenge': (6, 8), 'steal': (2, 4), 'con_layup': (7, 10), 'con_dunk': (3, 5), 'con_post': (4, 6), 'con_floater': (3, 5), 'con_mid': (2, 3), 'con_long': (2, 3), 'con_three': (2, 3)}
FOUL_RANGES = {'foul_steal': (6, 8), 'foul_contest': (7, 9)}  # lower is better: (highest above average, highest average)
def band(name, v):
    if name in FOUL_RANGES:
        h, a = FOUL_RANGES[name]; return 'H' if v <= h else ('A' if v <= a else 'L')
    a, h = RANGES[name]
    return 'H' if v >= h else ('A' if v >= a else 'L')

# Colours changed from the printed card to match the range chart (printed colour first), kept for the end-of-set cutoff review.
# D-184: entries for ratings whose range changed are removed (they no longer apply).
CHART_FIXES = [
 ('apgB','shot_dunk',17,'H','A'), ('apgB','con_layup',6,'A','L'),
]
# Provisional numbers (card printed colours only): stpfA defence = tier B + 1.
CHART_FIXES += []
