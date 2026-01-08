# Database Schema Documentation

The WireViz YAML Generator expects an SQLite database (`master.db`) with the following table structure:

## Table: NetTable

Stores point-to-point electrical connections.

| Column | Type | Description |
|--------|------|-------------|
| `cable_des` | TEXT | Cable designator (e.g., "W001") |
| `comp_des_1` | TEXT | Component designator at start (e.g., "J1") |
| `conn_des_1` | TEXT | Connector designator at start (e.g., "X1") |
| `pin_1` | TEXT | Pin number/name at start (e.g., "1", "A") |
| `comp_des_2` | TEXT | Component designator at end (e.g., "J2") |
| `conn_des_2` | TEXT | Connector designator at end (e.g., "") |
| `pin_2` | TEXT | Pin number/name at end (e.g., "2") |
| `net_name` | TEXT | Signal name (e.g., "+24V", "GND", "CAN_H") |

**Example Data:**
```sql
INSERT INTO NetTable VALUES 
('W001', 'JB1', 'X1', '1', 'BMU1', 'X1', 'J3', 'SignalA'),
('W001', 'JB1', 'X1', '2', 'BMU1', 'X1', 'J6', '+24V');
```

## Table: DesignatorTable

Maps component designators to physical connector part numbers.

| Column | Type | Description |
|--------|------|-------------|
| `comp_des` | TEXT | Component designator (e.g., "J1") |
| `conn_des` | TEXT | Connector designator (e.g., "X1") |
| `conn_mpn` | TEXT | Manufacturer Part Number for connector |

**Example Data:**
```sql
INSERT INTO DesignatorTable VALUES 
('JB1', 'X1', 'CONN-12345'),
('BMU1', 'X1', 'CONN-67890');
```

## Table: ConnectorTable

Connector catalog with specifications.

| Column | Type | Description |
|--------|------|-------------|
| `mpn` | TEXT | Manufacturer Part Number (unique key) |
| `pincount` | INTEGER | Number of pins in the connector |
| `mate_mpn` | TEXT | Mating connector part number |
| `pin_mpn` | TEXT | Pin/terminal part number |
| `description` | TEXT | Connector description |
| `manufacturer` | TEXT | Manufacturer name |

**Example Data:**
```sql
INSERT INTO ConnectorTable VALUES 
('CONN-12345', 10, 'MATE-12345', 'PIN-001', '10-Pin Header', 'Manufacturer A'),
('CONN-67890', 4, 'MATE-67890', 'PIN-002', '4-Pin Socket', 'Manufacturer B');
```

## Table: CableTable

Physical properties of cables.

| Column | Type | Description |
|--------|------|-------------|
| `cable_des` | TEXT | Cable designator (e.g., "W001") |
| `wire_gauge` | REAL | Wire gauge in mm² |
| `length` | REAL | Cable length in mm |
| `note` | TEXT | Construction notes or specifications |

**Example Data:**
```sql
INSERT INTO CableTable VALUES 
('W001', 0.5, 1500.0, 'Flexible PVC cable'),
('W002', 0.25, 800.0, 'Shielded twisted pair');
```

## Creating the Database

Use this SQL script to create a minimal working database:

```sql
CREATE TABLE NetTable (
    cable_des TEXT,
    comp_des_1 TEXT,
    conn_des_1 TEXT,
    pin_1 TEXT,
    comp_des_2 TEXT,
    conn_des_2 TEXT,
    pin_2 TEXT,
    net_name TEXT
);

CREATE TABLE DesignatorTable (
    comp_des TEXT,
    conn_des TEXT,
    conn_mpn TEXT
);

CREATE TABLE ConnectorTable (
    mpn TEXT PRIMARY KEY,
    pincount INTEGER,
    mate_mpn TEXT,
    pin_mpn TEXT,
    description TEXT,
    manufacturer TEXT
);

CREATE TABLE CableTable (
    cable_des TEXT PRIMARY KEY,
    wire_gauge REAL,
    length REAL,
    note TEXT
);
```

## Notes

- **Empty `conn_des`**: When `conn_des_2` is empty, only `comp_des_2` is used as the designator
- **Full Designator**: When both are present, the designator becomes `comp_des-conn_des` (e.g., "JB1-X1")
- **Net Names**: Should match the actual signal names in your electrical design
- **Wire Gauge**: Used for BOM calculation and cable specifications
- **Mate MPN**: The generator uses mate_mpn for connector images and metadata enrichment
