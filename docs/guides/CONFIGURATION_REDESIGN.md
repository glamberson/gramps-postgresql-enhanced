# PostgreSQL Enhanced Configuration Redesign

## Current Problems

1. **Per-database config files**: Each Gramps family tree directory gets its own `connection_info.txt`
2. **Ignored GUI parameters**: Host/port fields in GUI are not being used
3. **Monolithic mode confusion**: In monolithic mode, ALL trees share ONE database, so config should be universal

## Proper Configuration Priority (High to Low)

1. **GUI Parameters** (if provided in Gramps interface)
   - Host field
   - Port field  
   - Username field
   - Password field

2. **Central Config File** (for monolithic mode)
   - `~/.local/share/gramps/gramps60/plugins/PostgreSQLEnhanced/connection_info.txt`
   - OR environment variable: `GRAMPS_POSTGRESQL_CONFIG=/path/to/config.txt`

3. **Per-Tree Config** (for separate mode only)
   - `~/.local/share/gramps/grampsdb/{tree-id}/connection_info.txt`

4. **Defaults** (fallback)
   - host: localhost
   - port: 5432
   - user: gramps_user
   - password: gramps

## Configuration Logic

```python
def get_connection_config(directory, gui_params):
    config = load_defaults()
    
    # 1. Check database mode from central config
    central_config = load_central_config()
    database_mode = central_config.get('database_mode', 'separate')
    
    if database_mode == 'monolithic':
        # Use ONLY central config in monolithic mode
        config.update(central_config)
    else:
        # In separate mode, check per-tree config
        if directory and os.path.exists(f"{directory}/connection_info.txt"):
            tree_config = load_tree_config(directory)
            config.update(tree_config)
        else:
            config.update(central_config)
    
    # 2. Override with GUI parameters (highest priority)
    if gui_params.get('host'):
        config['host'] = gui_params['host']
    if gui_params.get('port'):
        config['port'] = gui_params['port']
    if gui_params.get('user'):
        config['user'] = gui_params['user']
    if gui_params.get('password'):
        config['password'] = gui_params['password']
    
    return config
```

## Implementation Changes Needed

1. **Modify `load()` method** to properly use GUI parameters
2. **Add central config location** check before per-tree config
3. **Respect database_mode** - don't create per-tree configs in monolithic mode
4. **Parse directory parameter** - might contain host:port info

## GUI Integration

The Gramps database selector likely passes connection info in the `directory` parameter as:
- Simple path: `/home/user/.local/share/gramps/grampsdb/xxx`
- Connection string: `postgresql://user:pass@host:port/dbname`
- Host:port:path: `192.168.10.90:5432:/path/to/tree`

Need to parse all these formats properly.