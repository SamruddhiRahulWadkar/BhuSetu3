# BhuSetu: 5-Minute Hackathon Judge Demo Script

**Project**: BhuSetu (भू-सेतु) - Intelligent Land Record Digitization and Validation System  
**Smart India Hackathon Problem Statement**: 26018  
**Nodal Ministry**: Department of Land Resources (DoLR), Ministry of Rural Development, Government of India  
**Target Audience**: Technical Evaluators, Revenue Department Officers, Senior Jury  

---

## Elevator Pitch (30 Seconds)

> *"India manages over 140 million agricultural land parcels, but legacy paper land records suffer from physical aging, regional dialect variations, mathematical fraud, and spatial discrepancies with cadastral maps.  
> **BhuSetu** solves this with an end-to-end AI and legal-logic architecture: multi-engine Indic vision extraction with regional term normalization, damage-aware calibrated confidence scoring, a configurable 10-rule statutory validation engine, forensic Error Level Analysis, GIS cadastral map cross-checking, and a cryptographically chained, tamper-evident audit ledger that supports dual-stage Maker-Checker workflows and DILRMP National MIS reporting."*

---

## Detailed 5-Minute Live Walkthrough

### ⏱️ Minute 0:00 – 0:45 | Ingestion, Immutability & Preprocessing

**Narrative**:  
*"We begin at the Ingestion and Preprocessing stage. Traditional systems risk data corruption when scans are modified. In BhuSetu, every incoming scan is assigned an immutable SHA-256 cryptographic digest before any processing begins."*

1. **Open Frontend**: Navigate to `http://localhost:5173/` (or click **Dashboard**).
2. **Show Upload View**: Click **Upload & Digitize** (`/upload`).
3. **Select Sample**: Choose `record_01.png` (Clean Hindi Khatauni) or `record_03.png` (Torn/Stained Marathi 7-12).
4. **Key Talking Points**:
   - Original file stored immutably in `data/storage/originals/` indexed by SHA-256.
   - Automatic multi-stage preprocessing: projection-profile deskewing, border cleanup, adaptive contrast normalization (CLAHE simulation), and tile-grid damage metrics (Laplacian blur variance, ink fade ratio, stain coverage).
   - Ingestion audit event recorded with predecessor hash.

---

### ⏱️ Minute 0:45 – 1:45 | Strict Object Extraction & Calibrated Confidence

**Narrative**:  
*"A critical invariant in BhuSetu: **never return bare strings**. Every extracted field is a structured object with value, raw_text, calibrated confidence breakdown, bounding box, and explainability flags."*

1. **Navigate to**: **Documents** (`/documents`) -> Click on `record_01.png` or `record_02.png` -> **Review** (`/documents/{id}`).
2. **Side-by-Side Reviewer**:
   - Left pane displays the scan with toggleable **BBoxes** and **Damage Tiles**.
   - Hover over a bounding box: notice green ($\ge 90\%$), amber ($60-89\%$), or red ($< 60\%$).
   - Click any field in the right panel: notice the **Source Scan Crop Preview** dynamically rendering the high-resolution optical snippet of that exact field.
3. **Demonstrate Regional Normalization**:
   - Show how Indic numerals (e.g. Devanagari `१४२/१`) are converted to ASCII `142/1`.
   - Show state-aware area unit conversion: Bigha in UP ($2529.28\text{ m}^2$) vs MP ($1337.8\text{ m}^2$), Guntha ($101.17\text{ m}^2$), Acre ($4046.86\text{ m}^2$) converted to standardized $\text{m}^2$ and hectares with explainability flags.
   - Show landowner name honorific stripping (श्री, श्रीमती, स्व.) and Latin transliteration.
4. **Highlight Multi-Factor Confidence Formula**:
   - $c = w_1 c_{\text{ocr}} + w_2 c_{\text{agree}} - w_3 p_{\text{damage}} + w_4 c_{\text{format}} + w_5 c_{\text{legal}}$
   - Explain intelligent routing: $\ge 0.90$ Auto-Accept, $0.60 - 0.89$ Field Review, $< 0.60$ Full Review.
   - Refer to `/docs/calibration.svg` showing empirical reliability curve with Expected Calibration Error $ECE = 0.0461$.

---

### ⏱️ Minute 1:45 – 2:45 | Legal-Logic Rule Engine & Master LRMS Hierarchy

**Narrative**:  
*"OCR alone cannot detect land fraud. BhuSetu includes a 10-rule legal-logic validation engine reading from declarative YAML rules, checking mathematical, temporal, statutory, and jurisdictional consistency."*

1. **In Document Reviewer**: Click the **Legal Rules** tab.
2. **Demonstrate Deliberate Fault Records**:
   - **Open `record_04.png`**: Trigger `RULE_SHARE_SUM_001` (Shares sum to $1.25 \ne 1.00$, over-allocation under Sec 44 TP Act).
   - **Open `record_05.png`**: Trigger `RULE_AREA_HOLDING_002` (Transferred area $12,000\text{ m}^2 > \text{Holding Area } 8,000\text{ m}^2$).
   - **Open `record_06.png`**: Trigger `RULE_MUTATION_CHRONOLOGY_003` (Mutation date predates deed registration date).
   - **Open `record_07.png`**: Trigger `RULE_PARTY_CAPACITY_004` (Transfer executed after recorded date of death).
   - **Open `record_08.png`**: Trigger `RULE_LAND_CLASS_NA_005` (Agricultural land converted to commercial without statutory NA order).
3. **Point out Statutory Disclaimer**:
   - Every rule output is labeled: `"advisory, not legal advice"`, safeguarding administrative sovereignty.
4. **Show Admin Rules Portal**:
   - Navigate to **Admin Rules** (`/admin-rules`).
   - Show how administrators can toggle rules, tune holding area thresholds or ceiling limits in real time with logged audit trails.

---

### ⏱️ Minute 2:45 – 3:30 | Cadastral GIS Cross-Check & ULPIN (Bhu-Aadhaar)

**Narrative**:  
*"A land record cannot be certified without spatial verification against the cadastral GIS layer."*

1. **Navigate to**: **Cadastre GIS** (`/map`).
2. **Interactive Map**:
   - Leaflet map displaying 40 vector parcel polygons loaded from `/data/cadastre/parcels.geojson`.
   - Click on parcel `27HA1001000101` (Survey No. 101, Wagholi).
   - The inspector panel opens on the right:
     - **ULPIN**: `27HA1001000101` (14-digit standard Bhu-Aadhaar).
     - **Recorded Area vs Polygon Area**: Computes metric planar area via geodesic equations ($111.13\text{ km/deg lat}$, $111.41 \times \cos(\text{lat})\text{ km/deg lon}$).
     - **Directional Boundary Check**: Cross-references adjacent survey numbers (North: 102, South: 105).
     - **Spatial Topology Sanity**: Flags sliver polygons, overlaps, or self-intersections.
3. **Area Discrepancy Alert**:
   - Show how parcels with $> 5\%$ deviation trigger a Warning, and $> 10\%$ trigger an Error requiring field survey remeasurement.

---

### ⏱️ Minute 3:30 – 4:15 | Forensic Tampering Scans & Physical Hints

**Narrative**:  
*"Digitization of historical documents is vulnerable to physical forgery—pasted stamps, overwritten numbers, and spliced text."*

1. **In Document Reviewer**: Click the **Forensics** tab.
2. **Examine Forensic Scans**:
   - **Error Level Analysis (ELA)**: Re-compresses image at $90\%$ quality and computes pixel-level delta. Highlight pasted revenue stamps where compression artifacts differ from background paper.
   - **Copy-Move Clone Detection**: Identifies repeated textures (e.g. cloned seal).
   - **Overwritten Digit Heuristic**: Flags sudden ink stroke intensity variance or double contours on survey numbers and areas.
3. **Legal Label**:
   - All flags strictly labeled: `"indicator for human review, not proof"`.

---

### ⏱️ Minute 4:15 – 5:00 | Maker-Checker Review & Cryptographic Audit Hash Chain

**Narrative**:  
*"To ensure total accountability, BhuSetu implements role-based access control, a two-stage Maker-Checker certification process, and an immutable SHA-256 hash-chained audit ledger."*

1. **Maker-Checker Flow**:
   - Log in as **Verifier / Patwari** (`verifier` / `verifier123`): Maker edits field, clicks **Submit Maker Review**. Document moves to `maker_reviewed`.
   - Log in as **Supervisor / SDO** (`supervisor` / `supervisor123`): SDO inspects maker diffs, adds certification notes, and clicks **Certify Title (Checker)**. Document moves to `published`.
2. **Tamper-Evident Audit Ledger**:
   - Navigate to **Audit Trail** (`/audit`).
   - Click **Verify Cryptographic Audit Chain**:
     - System executes `verify_audit_chain_integrity()`, traversing every block from the genesis block (`0000000000000000...`) to current block.
     - Green Badge: `"Cryptographic integrity verified across 47 audit blocks. Zero tampering detected."`
3. **DILRMP National MIS Sync**:
   - Click **DILRMP MIS Sync** in the navbar:
     - Real-time compliance metrics (RoR computerization rate, cadastral integration percentage, straight-through processing percentage) sent to National DILRMP MIS with acknowledgment ID.
4. **Export Land Records**:
   - Demonstrate `GET /api/v1/records/export?format=geojson` and `format=csv`.
   - Show citizen PII (Aadhaar `XXXX-XXXX-9012`, names `R****h K***r`) automatically masked when accessed by read-only API clients.

---

## Quick Reference of Demo Accounts

| Role | Username | Password | Key Capability Shown |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin` | `admin123` | Validation rule toggle, threshold tuning, system export |
| **Supervisor / SDO** | `supervisor` | `supervisor123` | Maker-checker stage 2 certification, DILRMP sync |
| **Verifier (Maker)** | `verifier` | `verifier123` | Low-confidence field review, maker stage submission |
| **Data Operator** | `operator` | `operator123` | Ingestion, scan upload, OCR monitoring |
| **Auditor** | `auditor` | `auditor123` | Read-only audit ledger, hash chain verification |
| **Read-Only API** | `readonly_api` | `apiclient123` | Scoped external API queries with citizen PII masking |

---

## 5 Fault Injections to Highlight to the Judges

1. **`record_04.png`**: Shares sum = $0.50 + 0.75 = 1.25 \ne 1.00$ (**Over-allocation fraud**)
2. **`record_05.png`**: Transferred area $1.20\text{ ha} > \text{Holding area } 0.80\text{ ha}$ (**Over-conveyance fraud**)
3. **`record_06.png`**: Mutation dated 2019-01-10 with deed registered 2021-03-15 (**Chronology violation**)
4. **`record_07.png`**: Deceased party executed transfer 3 years after death date (**Post-mortem execution**)
5. **`record_08.png`**: Agricultural land marked Commercial without statutory order (**Illegal NA conversion**)
