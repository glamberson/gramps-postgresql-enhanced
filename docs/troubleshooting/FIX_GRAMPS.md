# Fix for Gramps ResourcePath Error

The error `ResourcePath.ERROR: Unable to determine resource path` occurs when Gramps can't find its data files.

## Quick Fix

Run ONE of these commands in your terminal:

### Option 1: Exit virtual environment and run system Gramps
```bash
deactivate
/usr/bin/gramps
```

### Option 2: Run Gramps from source directory
```bash
cd /home/greg/genealogy-ai/gramps-project-gramps-e960164
python3 -m gramps
```

### Option 3: Set resource path explicitly
```bash
GRAMPS_RESOURCES=/usr/share/gramps gramps
```

## Permanent Fix

Add this to your `~/.bashrc`:

```bash
# Gramps alias to handle virtual environments
alias gramps='(command -v deactivate &>/dev/null && deactivate; /usr/bin/gramps)'

# Or if running from source
alias gramps='cd /home/greg/genealogy-ai/gramps-project-gramps-e960164 && python3 -m gramps'
```

Then reload your shell:
```bash
source ~/.bashrc
```

## Why This Happens

1. You're in a virtual environment (`ancestry-seleniumbase`) which changes Python paths
2. Gramps can't find its resource files when run from a venv
3. The GRAMPS_RESOURCES environment variable isn't set

## Testing the PostgreSQL Enhanced Addon

Once Gramps is running, follow the testing instructions in:
`/home/greg/gramps-postgresql-enhanced/TESTING.md`