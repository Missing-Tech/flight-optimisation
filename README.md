# Flight path optimisation to avoid contrails using the Ant Colony algorithm

## Start program

1. Create a .venv from the root directory

```bash
virtualenv .venv
```

2. Activate the .venv

```bash
source .venv/bin/activate
```

3. Install packages

```bash
pip install -r requirements.txt
```

4. Run the program

```bash
python main.py
```

## Tests

Run tests for all modules with:

```bash
python -m unittest discover -s . -p "test_*.py"
```
