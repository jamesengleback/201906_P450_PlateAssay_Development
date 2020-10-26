### Iteration round 6
##### Background
In the last tests I did 9 repeats of my substrates arachadonic acid and 4-phenylimidazole. It was  repeats in the mother plate to test for mixing variability and stuff like that. I got really consistent results with arachadonic acid, which was great, but terrible results with 4-phenylimidazole.

I haven't got to the bottom of that yet, but today I'm going to work on fatty acids and try to get a few of them working with a few repeats of each. I have a few socks of each, so I may as well use all of them to see which is good and which is donked.

Substrates:
* Arachadonic acid
* Lauric acid
* Palmitic acid

That should do for now. I can do 3 reps of each in the mother plate which will serve 6 reps per substrate in the assay plate total.

Here's my layout:
![](/home/james/Documents/Work/201906_PlateAssayDevelopment/6_More_iterationns/20190620_1_Platelayout.png)
Same as before, light squares are protein-free controls. Each double column rep is a sing column from the mother plate. I would do three but I can't.

P450 BM3 WT Heme concentration:
* [Data](20190620_BM3conccheck.csv) from a Cary UV-Vis Spectrometer
* [Script](ProtinConcCheck.py) to calculate protein concentration
```
$ python3 ProtinConcCheck.py
0   -0.006898
1    3.869643
Name: P450 conc/uM, dtype: float64
```
* conc = 3.86 uM

It felt like I didn't mess up the pipetting. Used a lot of tips though, so to try to limit that, I pipetted out the compounds first, changing tips between mother plate reps. Added buffer to the blank wells without mixing so that I could use a single row of tips. Same for the protein, being really careful to not let the tips touch the inside of the wells. Then to mix, I pipetted up and down from the low concentrations upward for the protein wells and the buffer wells (seperately) under the assumption that any substrate carried to the next concentration up shouldn't have a big effect. I hope. It saved a lot of tips but Ill see what I can do to make it more efficient.

Carried the whole affair downstairs in my homemade plate carrier
![](assets/readme-c8e5a655.jpg)

* Plate type: Corning 3660 (check)

And then span at 4000 rpm for 2 mins. Not sure how much is enough, should find that out.
Scanned the wells for wavelengths 220-800 nm on the Pherastar FS. It took about 3 mins, plus some extra time to transfer the data to the dedicated PC, and then to Open it. I wonder what file type it transfers as, because as an ASCII csv file it opens and transfers really quick. That's one to ask BMG if I ever get the chance.

* Platereader [data](assets/readme-00111b7f.CSV)
* This old [script](Plateanalysis20190620.py) agian!

*Arachadonic Acid* Looks good again

|Corrected Specs| Difference Specs| Michaelis Menten Curves|
|---------|---------|---------|
|![](arachadnic_acid_1.1_Corrected_Spectra_PM.png)|![](arachadnic_acid_1.1_Difference_Spectra_PM.png) | ![](arachadnic_acid_1.1_Michaelis_Menten_PM.png)|
|![](arachadnic_acid_1.2_Corrected_Spectra_PM.png) | ![](arachadnic_acid_1.2_Difference_Spectra_PM.png) | ![](arachadnic_acid_1.2_Michaelis_Menten_PM.png)|
|![](arachadnic_acid_2.1_Corrected_Spectra_PM.png)|![]( arachadnic_acid_2.1_Difference_Spectra_PM.png)| ![](arachadnic_acid_2.1_Michaelis_Menten_PM.png)|
|![](arachadnic_acid_2.2_Corrected_Spectra_PM.png)|![]( arachadnic_acid_2.2_Difference_Spectra_PM.png)| ![](arachadnic_acid_2.2_Michaelis_Menten_PM.png)|
|![](arachadnic_acid_3.1_Corrected_Spectra_PM.png)|![]( arachadnic_acid_3.1_Difference_Spectra_PM.png)| ![](arachadnic_acid_3.1_Michaelis_Menten_PM.png)|
|![](arachadnic_acid_3.2_Corrected_Spectra_PM.png)|![]( arachadnic_acid_3.2_Difference_Spectra_PM.png)| ![](arachadnic_acid_3.2_Michaelis_Menten_PM.png)|

**Palmitic acid** sucks

|Corrected Specs| Difference Specs| Michaelis Menten Curves|
|---------|---------|---------|
|![](Palmitic_acid_1.1_Corrected_Spectra_PM.png)|![](Palmitic_acid_1.1_Difference_Spectra_PM.png) | ![](Palmitic_acid_1.1_Michaelis_Menten_PM.png)|
|![](Palmitic_acid_1.2_Corrected_Spectra_PM.png) | ![](Palmitic_acid_1.2_Difference_Spectra_PM.png) | ![](Palmitic_acid_1.2_Michaelis_Menten_PM.png)|
|![](Palmitic_acid_2.1_Corrected_Spectra_PM.png)|![]( Palmitic_acid_2.1_Difference_Spectra_PM.png)| ![](Palmitic_acid_2.1_Michaelis_Menten_PM.png)|
|![](Palmitic_acid_2.2_Corrected_Spectra_PM.png)|![]( Palmitic_acid_2.2_Difference_Spectra_PM.png)| ![](Palmitic_acid_2.2_Michaelis_Menten_PM.png)|
|![](Palmitic_acid_3.1_Corrected_Spectra_PM.png)|![]( Palmitic_acid_3.1_Difference_Spectra_PM.png)| ![](Palmitic_acid_3.1_Michaelis_Menten_PM.png)|
|![](Palmitic_acid_3.2_Corrected_Spectra_PM.png)|![]( Palmitic_acid_3.2_Difference_Spectra_PM.png)| ![](Palmitic_acid_3.2_Michaelis_Menten_PM.png)|

**Lauric Acid** sucks too.

|Corrected Specs| Difference Specs| Michaelis Menten Curves|
|---------|---------|---------|
|![](Lauric_acid_1.1_Corrected_Spectra_PM.png)|![](Lauric_acid_1.1_Difference_Spectra_PM.png) | ![](Lauric_acid_1.1_Michaelis_Menten_PM.png)|
|![](Lauric_acid_1.2_Corrected_Spectra_PM.png) | ![](Lauric_acid_1.2_Difference_Spectra_PM.png) | ![](Lauric_acid_1.2_Michaelis_Menten_PM.png)|
|![](Lauric_acid_2.1_Corrected_Spectra_PM.png)|![]( Lauric_acid_2.1_Difference_Spectra_PM.png)| ![](Lauric_acid_2.1_Michaelis_Menten_PM.png)|
|![](Lauric_acid_2.2_Corrected_Spectra_PM.png)|![]( Lauric_acid_2.2_Difference_Spectra_PM.png)| ![](Lauric_acid_2.2_Michaelis_Menten_PM.png)|
|![](Lauric_acid_3.1_Corrected_Spectra_PM.png)|![]( Lauric_acid_3.1_Difference_Spectra_PM.png)| ![](Lauric_acid_3.1_Michaelis_Menten_PM.png)|
|![](Lauric_acid_3.2_Corrected_Spectra_PM.png)|![]( Lauric_acid_3.2_Difference_Spectra_PM.png)| ![](Lauric_acid_3.2_Michaelis_Menten_PM.png)|

It looks like Lauric and Palmitic acids aren't introducing a shift at all. Here are some potential reasons:
1. **These things aren't even substrates anyway (easy to check in literature)**
2. **These things are precipitating**
3. **I made up my stocks wrong**
4. **The fatty acids are sticking to the lipophilic plate surface (I'm still using the treated plates because they're in plentiful suppy)**

### I'm going to adress these 1 by 1

###### 1. These things aren't even substrates anyway
Pretty sure they are, put some evidence in here. I think I have some titrations on my drive.


###### 2. These things are precipitating
```python
>>> from rdkit import Chem
>>> aracadonic_acid = Chem.MolFromSmiles('CCCCCC=CCC=CCC=CCC=CCCCC(=O)O')
>>> lauric_acid = Chem.MolFromSmiles('CCCCCCCCCCCC(=O)O')
>>> palmitic_acid = Chem.MolFromSmiles('CCCCCCCCCCCCCCCC(=O)O')
>>> help(Chem)

>>> aracadonic_acid = Chem.AddHs(aracadonic_acid)
>>> lauric_acid = Chem.AddHs(lauric_acid)
>>> palmitic_acid = Chem.AddHs(palmitic_acid)
>>> Descriptors.MolLogP(aracadonic_acid)
6.216700000000006
>>> Descriptors.MolLogP(lauric_acid)
3.991900000000002
>>> Descriptors.MolLogP(palmitic_acid)
5.552300000000005
```
It's probably not a LogP problem

##### 3. I made up my stocks wrong
Probably this one, I can test this by repeating my experiment tomorrow with fresh stocks to see what's up.

##### 4. Sticking to the plates
Could be this if I rule out the above
