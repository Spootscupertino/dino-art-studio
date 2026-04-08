-- Dinosaur Art Prompt Engineering System
-- Schema for SQLite

PRAGMA foreign_keys = ON;

-- Dinosaur species reference data
CREATE TABLE IF NOT EXISTS species (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    name                     TEXT NOT NULL UNIQUE,
    common_name              TEXT,
    period                   TEXT CHECK(period IN ('Devonian', 'Carboniferous', 'Permian', 'Triassic', 'Jurassic', 'Cretaceous', 'Miocene', 'Other')),
    diet                     TEXT CHECK(diet IN ('Carnivore', 'Herbivore', 'Omnivore', 'Piscivore', 'Filter-feeder')),
    size_class               TEXT CHECK(size_class IN ('Tiny', 'Small', 'Medium', 'Large', 'Massive')),
    description              TEXT,
    notes                    TEXT,
    habitat                  TEXT CHECK(habitat IN ('terrestrial', 'marine', 'aerial')) DEFAULT 'terrestrial',
    -- Scientific accuracy data
    body_length_m            REAL,
    body_mass_kg             REAL,
    locomotion_type          TEXT,
    feathering_coverage      TEXT CHECK(feathering_coverage IN ('none','partial','full','uncertain')),
    skin_texture_type        TEXT,
    tail_posture             TEXT,
    wrist_position           TEXT,
    known_coloration_evidence TEXT,
    primary_fossil_sites     TEXT,
    key_papers               TEXT,
    last_scientific_update   INTEGER,
    created_at               TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Reusable prompt parameter definitions (style axes, modifiers, etc.)
CREATE TABLE IF NOT EXISTS parameters (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category     TEXT NOT NULL,   -- e.g. 'style', 'lighting', 'camera', 'medium', 'mood'
    name         TEXT NOT NULL,
    value        TEXT NOT NULL,   -- the actual token/phrase injected into prompts
    weight       REAL DEFAULT 1.0 CHECK(weight BETWEEN 0.0 AND 2.0),
    description  TEXT,
    habitats     TEXT DEFAULT 'terrestrial,marine,aerial',  -- comma-separated habitat list
    UNIQUE(category, name)
);

-- Art prompts
CREATE TABLE IF NOT EXISTS prompts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id       INTEGER REFERENCES species(id) ON DELETE SET NULL,
    title            TEXT NOT NULL,
    positive_prompt  TEXT NOT NULL,
    negative_prompt  TEXT,
    version          INTEGER NOT NULL DEFAULT 1,
    parent_id        INTEGER REFERENCES prompts(id) ON DELETE SET NULL,
    tags             TEXT,        -- comma-separated tags for filtering
    status           TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'generated', 'archived')),
    is_template      INTEGER NOT NULL DEFAULT 0 CHECK(is_template IN (0, 1)),
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Many-to-many: which parameters are active on a given prompt
CREATE TABLE IF NOT EXISTS prompt_parameters (
    prompt_id    INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    parameter_id INTEGER NOT NULL REFERENCES parameters(id) ON DELETE CASCADE,
    override_weight REAL,        -- NULL means use parameters.weight
    PRIMARY KEY (prompt_id, parameter_id)
);

-- Generation results (one row per image/output produced)
CREATE TABLE IF NOT EXISTS results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id       INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    model           TEXT NOT NULL DEFAULT 'midjourney',
    image_path      TEXT,        -- local file path or URL
    seed            INTEGER,
    mj_version      TEXT,        -- e.g. '6.1', '6', '5.2', 'niji 6'
    stylize         INTEGER CHECK(stylize BETWEEN 0 AND 1000),   -- --stylize (default 100)
    chaos           INTEGER CHECK(chaos BETWEEN 0 AND 100),      -- --chaos   (default 0)
    aspect_ratio    TEXT,        -- e.g. '16:9', '1:1', '3:2'   -- --ar
    style           TEXT CHECK(style IN ('raw', 'default')),     -- --style
    quality         REAL CHECK(quality IN (0.25, 0.5, 1.0)),     -- --q
    resolution      TEXT,        -- final output dimensions, e.g. '1456x816'
    rating          INTEGER CHECK(rating BETWEEN 1 AND 5),
    notes           TEXT,
    generated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Peer-reviewed research notes per species (findings that may affect prompt accuracy)
CREATE TABLE IF NOT EXISTS research_notes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id   INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
    finding      TEXT NOT NULL,
    source       TEXT,
    year         INTEGER,
    author       TEXT,
    doi          TEXT,
    affects_prompt INTEGER NOT NULL DEFAULT 1 CHECK(affects_prompt IN (0, 1)),
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_research_notes_species ON research_notes(species_id);

-- Species-specific required parameters (auto-applied when that species is selected)
CREATE TABLE IF NOT EXISTS species_parameters (
    species_id   INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
    parameter_id INTEGER NOT NULL REFERENCES parameters(id) ON DELETE CASCADE,
    required     INTEGER NOT NULL DEFAULT 1 CHECK(required IN (0, 1)),
    PRIMARY KEY (species_id, parameter_id)
);

-- Global accuracy rules appended to every generated prompt
CREATE TABLE IF NOT EXISTS global_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL DEFAULT 'accuracy',
    rule        TEXT NOT NULL UNIQUE,
    description TEXT,
    active      INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_prompts_species   ON prompts(species_id);
CREATE INDEX IF NOT EXISTS idx_prompts_parent    ON prompts(parent_id);
CREATE INDEX IF NOT EXISTS idx_results_prompt    ON results(prompt_id);
CREATE INDEX IF NOT EXISTS idx_results_rating    ON results(rating);
CREATE INDEX IF NOT EXISTS idx_parameters_cat    ON parameters(category);
