# last development experiment

## background

- it's pandemic, and I'm running out of PhD time. I need this assay up and
  running quick
- restrictions: Between-floor movement is restricted, so it's not as easy for me
  to access the echo, multidrop or platereaders with injectors that I need.
- options:
	- secure access to the echo and injection plate reader. carry out validation
	  & screening experiments there. so far I may have access to the Cai Echo
	  via Josh - who's leaving the country around christmas I think. I'm working
	  on access to the Synbio platereader.
		-	advantage: assay precision - the echo and the plate reader injection
			are about as precise as I can hope for
		- advantage: automation - the synbio plate reader has a stacker, so I
		  could queue a few plates per batch. Dispensing compounds & dmso in the
		  echo is fairly straightforward and I can do that in advance. Manual
		  handling errors will be low
		- advantage - no need to centrifuge out bubbles - plate injectors don't
		  normally make them
		- disadvantage: relies on access to 2 machines on different floor. I'm
		  not sure how in-use the plate reader is, but it could be an issue
	- assay manually - dispense master stocks of compounds by hand, then serial
	  dilute and add protein with a multichannel. read on the Feilds' group
	  platereader
		- advantage: minimise reliance on machines, only one plate reader.
		- disadvantage: require de-lidders for master stocks. travel to floor 1
		- disadvantage - pipetting errors - in the past, slight differences
		  between channels in pipettes has lead to errors. manual handling
		  errors will be expensive
		- disadvantage - need to spin plates to move bubbles - time consuming +
		  would need to borrow plate holders for centrifuge
- choice: access to automation is preferable, manual prep is a last resort. I
  should test both for just in case. Also, testing manually can be a pilot run.

#### dump assays

- I'll need to set up dump assays - a quick Y/n for compounds similar to Laura's
  spin shift titration. I could probably validate it against her data. I think
  I'll sort this out after I've found a good vol/protein conc balance wrt signal
  strength

## aim

#### optimize

- accuracy - vs titrations - target = kd
- signal strength / sensitivity - R^2 * vmax

### free params

- assay vol - range: 20, 30, 40 µl
- enzyme conc - range: 10, 15, 20 µM

### fixed params

- K = 3 - +ve correlation with K and R2 in previous tests (might be compound
  specific) - 3 is about as high as i can get away with
- dmso - 5% - as much as I can get away with - increases error though

### compounds

- arachadonic acid
- lauric acid
- palmitic acid
- 4-phenyl imidazole
- sds
- -ve ctrl

#### test:

- effect of vol on sensitivity
- effect of conc on sensitivity
- whilst also validating the assay - pick best
