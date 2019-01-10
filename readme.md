roles
=======

Code for a topic-modeling variant that allows the emergence of character-level "roles" as well as book-level "themes."

Very simply

**infer_roles.py** is the main script. (Short name for convenience; it infers themes as well as roles.)

and **gibbs.py** is a module that gets called in multiprocessing to permit parallelizing the inference.