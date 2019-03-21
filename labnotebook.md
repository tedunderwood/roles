lab notebook
=============

Model **firstresult** was run on on tinyfic.txt using 60 themes and 120 roles. Vicabulary was 50000 words. Alpha was set to .0007 and was not optimized. Beta was 0.1. There were 250 iterations (not enough).

Model **secondresult** was run on tinyfic.txt using 60 themes and 160 roles. Vocabulary was 64000 words. Alpha was set to .0003 and was not optimized. Beta was 0.1. We gave it 500 iterations.

Jan 10, 2019
------------
Successful results from **firstresult.** Base accuracy 76.6%; higher if document centroids are subtracted.

Model **thirdresult** was run on tinyfic.txt using 80 themes and 160 roles. Vocabulary was 70000 words. Alpha was set to .0002 and was not optimized; beta 0.1. 450 iterations.

Jan 13, 2019
------------

**fourthresult**

    python3 infer_roles.py -source bestfic.txt -iterations 200 -roles 150 -themes 50 -words 72000 -alpha .0004 -name fourthmodel -numprocesses 18 -maxlines 500000

Switched the source to bestfic. 150 roles and 50 themes for a 3/1 ratio. Alpha slightly higher.

**fifthresult**
We'll keep a 3-1 ratio but reduce the overall number of topics. 120 roles and 40 themes. Stick with 72000 words and see if we can keep that constant in the future.

    python3 infer_roles.py -source bestfic.txt -iterations 250 -roles 120 -themes 40 -words 72000 -alpha .0005 -name fifthmodel -numprocesses 18 -maxlines 500000

**sixthresult**
Keep a 3-1 ratio and increase overall number of topics. 180 roles and 60 themes.

    python3 infer_roles.py -source bestfic.txt -iterations 250 -roles 180 -themes 60 -words 72000 -alpha .0005 -name sixthmodel -numprocesses 18 -maxlines 500000

**seventhresult**
Try a 2-1 ratio with 60 themes. Also use an alpha setting like the one used in **secondresult,** but apply to bestfic.txt.

    python3 infer_roles.py -source bestfic.txt -iterations 300 -roles 120 -themes 60 -words 72000 -alpha .0003 -name seventhmodel -numprocesses 18 -maxlines 500000

January 26, 2019
----------------

**bioficA**
Using the settings for **sixthresult** (which seem to be the best so far), but applying them to a dataset that combines roughly equal amounts of biography and fiction.

    python3 infer_roles.py -source bestbiofic.txt -iterations 250 -roles 180 -themes 60 -words 72000 -alpha .0005 -name bioficA -numprocesses 15 -maxlines 800000

**bioA**
Using the settings for **sixthresult**, but applying them to a dataset of biography alone (plus a tiny amount of fiction needed to test hypotheses).

    python3 infer_roles.py -source bestbio.txt -iterations 250 -roles 180 -themes 60 -words 72000 -alpha .0005 -name bioA -numprocesses 15 -maxlines 1100000

March 21, 2019
--------------

**eighthmodel**
Might as well be called nullmodel. Basically a way of running infer_roles as if it were generic LDA, with no themes and just character-level roles.

    python3 infer_roles.py -source bestfic.txt -iterations 250 -roles 240 -themes 0 -words 72000 -alpha .0005 -name eighthmodel -numprocesses 18 -maxlines 500000
