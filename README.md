# How to run instrument simulation 
open another terminal and run command </br>

```$>py .\src\engine\virtual_scope.py```


# How to install python package:

1. cd into interpreter folder. (ie. c:\python38 or c:\<project>\.venv)

```terminal
    > cd c:\ATS 
```

2. activate virtual environment if used (otherwise ignore this section)

```terminal
    > .venv\Scripts\activate 
```

3. Set proxy

```terminal
    > .venv\Scripts\setProxy.bat 
```

4. Set proxy

```terminal
    > pip install XYZ 
```


# How to generate venv

1. Create the virtual environment from the project root:

```terminal
    > python -m venv .venv
```
2. Activate the venv

Windows CMD
```terminal
    > .venv\Scripts\activate
```


PowerShell
```terminal
    > .\.venv\Scripts\Activate.ps1
```

Git Bash
```terminal
    > source .venv/Scripts/activate
```




# How to create pip requirement 

1. Create requirements.txt from the project root:

```terminal
    > pip freeze > requirements.txt
```

2. Install requirements.txt from the project root:

```terminal
    > pip install -r requirements.txt
```

