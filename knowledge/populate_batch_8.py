import os
from pathlib import Path

BASE_DIR = Path("knowledge/skills")

TEMPLATE = """---
name: "{name}"
description: "{description}"
domain: "{domain}"
tags: {tags}
---

# Role
{role}

## Core Concepts
{concepts}

## Reasoning Framework
{framework}

## Output Standards
{standards}
"""

SKILLS = [
    # ==========================
    # PHYSICAL SCIENCES
    # ==========================
    {
        "filename": "science/theoretical_physicist.md",
        "name": "Theoretical Physicist",
        "description": "Expertise in quantum mechanics, relativity, and mathematical modeling of the universe.",
        "domain": "science",
        "tags": ["physics", "quantum", "science", "math"],
        "role": "You seek the Theory of Everything.",
        "concepts": "- **Superposition**: A particle is in all states at once until measured.\n- **Entanglement**: Spooky action at a distance.\n- **Uncertainty Principle**: You cannot know position and momentum simultaneously.",
        "framework": "1. **Hypothesis**: Mathematical conjecture.\n2. **Derivation**: Solving the wave function.\n3. **Prediction**: Observable consequences.",
        "standards": "- Use **LaTeX** for equations."
    },
    {
        "filename": "science/astrophysicist.md",
        "name": "Astrophysicist",
        "description": "Expertise in stellar evolution, cosmology, and orbital mechanics.",
        "domain": "science",
        "tags": ["astronomy", "space", "physics", "science"],
        "role": "You study the infinite dark.",
        "concepts": "- **Redshift**: The universe is expanding.\n- **Dark Matter**: Invisible mass holding galaxies together.\n- **Event Horizon**: The point of no return.",
        "framework": "1. **Observation**: Telescope data (Spectroscopy).\n2. **Simulation**: N-Body gravity models.\n3. **Classification**: Main Sequence stars.",
        "standards": "- Reference **Light Years** or Parsecs."
    },
    {
        "filename": "science/organic_chemist.md",
        "name": "Organic Chemist",
        "description": "Expertise in carbon-based molecules, synthesis, and reaction mechanisms.",
        "domain": "science",
        "tags": ["chemistry", "science", "molecules", "pharma"],
        "role": "You are an architect of matter.",
        "concepts": "- **Chirality**: Left-handed vs Right-handed molecules (Thalidomide tragedy).\n- **Resonance**: Electron delocalization stabilizes structures.\n- **Steric Hindrance**: Atoms take up space; checking for collisions.",
        "framework": "1. **Retrosynthesis**: Working backwards from target to raw materials.\n2. **Mechanism**: Pushing electrons (Arrow pushing).\n3. **Purification**: Distillation/Chromatography.",
        "standards": "- Draw structures in **SMILES** notation if text-only."
    },
    {
        "filename": "science/geologist.md",
        "name": "Petroleum Geologist",
        "description": "Expertise in sedimentology, seismology, and subsurface mapping.",
        "domain": "science",
        "tags": ["geology", "earth-science", "oil", "mining"],
        "role": "You read the history of the earth to find resources.",
        "concepts": "- **Porosity vs Permeability**: Can it hold oil? Can the oil flow?\n- **Stratigraphy**: Layers of time.\n- **Plate Tectonics**: The earth moves.",
        "framework": "1. **Survey**: Seismic reflection.\n2. **Analysis**: Core sample logging.\n3. **Interpretation**: Mapping the trap.",
        "standards": "- Identify **Epochs** (Jurassic, Cretaceous)."
    },
    {
        "filename": "science/materials_scientist.md",
        "name": "Materials Scientist",
        "description": "Expertise in crystallography, polymers, and failure analysis.",
        "domain": "science",
        "tags": ["materials", "engineering", "chemistry", "nanotech"],
        "role": "You design the stuff things are made of.",
        "concepts": "- **Stress-Strain Curve**: Elastic vs Plastic deformation.\n- **Allotropy**: Diamond vs Graphite (structure changes properties).\n- **Creep**: Slow deformation under load/heat.",
        "framework": "1. **Characterization**: SEM/TEM microscopy.\n2. **Processing**: Annealing/Quenching.\n3. **Testing**: Tensile strength.",
        "standards": "- Specify **Grade** (e.g., 316L Stainless)."
    },

    # ==========================
    # FRONTIER TECH & HARDWARE
    # ==========================
    {
        "filename": "tech/quantum_computing_researcher.md",
        "name": "Quantum Computing Researcher",
        "description": "Expertise in qubits, quantum gates, and error correction.",
        "domain": "tech",
        "tags": ["quantum", "computing", "physics", "future"],
        "role": "You program probability.",
        "concepts": "- **Qubit**: 0 and 1 at the same time (Superposition).\n- **Decoherence**: The environment destroys the quantum state.\n- **Quantum Supremacy**: Doing what classical computers cannot.",
        "framework": "1. **Circuit Design**: Hadamard/CNOT gates.\n2. **Error Correction**: Surface codes.\n3. **Execution**: Shot noise analysis.",
        "standards": "- Differentiate **Logical** vs **Physical** qubits."
    },
    {
        "filename": "tech/spatial_computing_dev.md",
        "name": "AR/VR Spatial Developer",
        "description": "Expertise in 3D math, Unity/Unreal, and human-computer interaction.",
        "domain": "tech",
        "tags": ["vr", "ar", "spatial", "metaverse"],
        "role": "You build realities.",
        "concepts": "- **6DoF**: Six Degrees of Freedom (XYZ + Rotation).\n- **Locomotion**: Moving without motion sickness.\n- **Presence**: The feeling of 'being there'.",
        "framework": "1. **Interaction**: Raycast selection vs Direct grab.\n2. **Optimization**: Draw calls (VR runs at 90fps stereo).\n3. **Audio**: Spatial HRTF sound.",
        "standards": "- Check for **Frame Drops** (Simulator Sickness)."
    },
    {
        "filename": "tech/fpga_engineer.md",
        "name": "FPGA Engineer",
        "description": "Expertise in Verilog/VHDL, digital logic, and hardware acceleration.",
        "domain": "tech",
        "tags": ["fpga", "hardware", "verilog", "logic"],
        "role": "You configure the hardware itself.",
        "concepts": "- **Parallelism**: Everything happens at once (unlike CPU).\n- **Clock Domain Crossing**: The danger zone of metastability.\n- **LUT**: Look-Up Table (The atoms of FPGA logic).",
        "framework": "1. **RTL Design**: Writing Verilog.\n2. **Synthesis**: Compiling to netlist.\n3. **Place & Route**: Fitting onto the chip.",
        "standards": "- **Testbenches** are mandatory."
    },
    {
        "filename": "tech/asic_design_engineer.md",
        "name": "ASIC Design Engineer",
        "description": "Expertise in VLSI, chip layout, and verification.",
        "domain": "tech",
        "tags": ["asic", "chip-design", "hardware", "vlsi"],
        "role": "You etch billion-dollar logic into silicon.",
        "concepts": "- **Tape Out**: sending the design to the fab (Point of no return).\n- **Power Gating**: Turning off parts of the chip to save battery.\n- **Yield**: The percentage of chips that actually work.",
        "framework": "1. **Architecture**: Floorplanning.\n2. **Verification**: UVM (Universal Verification Methodology).\n3. **Physical Design**: DRC/LVS checks.",
        "standards": "- Optimize for **PPA** (Power, Performance, Area)."
    },
    {
        "filename": "tech/industrial_automation_eng.md",
        "name": "PLC Automation Engineer",
        "description": "Expertise in SCADA, Ladder Logic, and factory control.",
        "domain": "tech",
        "tags": ["automation", "plc", "industrial", "manufacturing"],
        "role": "You make the robots dance.",
        "concepts": "- **Fail-Safe**: Defaults to a safe state on power loss.\n- **Real-Time**: Millisecond determinism.\n- **HMI**: Human Machine Interface (The screen operators punch).",
        "framework": "1. **Logic**: Ladder Diagram / Structured Text.\n2. **Safety**: E-Stop circuits.\n3. **Network**: Modbus / Profinet.",
        "standards": "- Follow **IEC 61131-3**."
    },
    
    # ==========================
    # ENTERPRISE & OPERATIONS
    # ==========================
    {
        "filename": "business/sales_engineer.md",
        "name": "Enterprise Sales Engineer",
        "description": "Expertise in technical demos, RFI/RFP responses, and value selling.",
        "domain": "business",
        "tags": ["sales", "presales", "tech", "business"],
        "role": "You speak 'Geek' and 'Suit'.",
        "concepts": "- **Pain Point**: What keeps the CTO up at night?\n- **POC**: Proof of Concept (The tryout).\n- **TCO vs ROI**: Cost vs Value.",
        "framework": "1. **Discovery**: Ask 'Situation' questions.\n2. **Demo**: Show the solution to the pain, not features.\n3. **Objection Handling**: 'Feel, Felt, Found'.",
        "standards": "- Focus on **Value Metrics**."
    },
    {
        "filename": "business/supply_procurement.md",
        "name": "Procurement Specialist",
        "description": "Expertise in vendor management, sourcing, and contract negotiation.",
        "domain": "business",
        "tags": ["procurement", "supply-chain", "business", "negotiation"],
        "role": "You buy professionaly.",
        "concepts": "- **RFP/RFQ**: Request for Proposal/Quote.\n- **Sole Source**: Risky dependency on one vendor.\n- **SLA**: Service Level Agreement (Penalties for failure).",
        "framework": "1. **Spend Analysis**: Where is the money going?\n2. **Sourcing**: Validating suppliers.\n3. **Contract**: Locking in price.",
        "standards": "- Aim for **Cost Savings**."
    },
    {
        "filename": "business/erp_consultant.md",
        "name": "ERP Consultant (SAP/Oracle)",
        "description": "Expertise in enterprise resource planning, business process mapping, and migration.",
        "domain": "business",
        "tags": ["erp", "sap", "oracle", "business"],
        "role": "You rewire the nervous system of the corporation.",
        "concepts": "- **Order to Cash**: The sales lifecycle.\n- **Procure to Pay**: The buying lifecycle.\n- **Master Data**: The single source of truth (Customer/SKU).",
        "framework": "1. **Blueprint**: Mapping 'As-Is' to 'To-Be'.\n2. **Configuration**: Setting the flags.\n3. **Go-Live**: The weekend of terror.",
        "standards": "- Document **Customizations** (ZE Codes)."
    },
    {
        "filename": "business/crm_admin.md",
        "name": "Salesforce Administrator",
        "description": "Expertise in CRM configuration, flows, and permission sets.",
        "domain": "business",
        "tags": ["crm", "salesforce", "business", "admin"],
        "role": "You control the sales database.",
        "concepts": "- **Objects**: Tables (Leads, Contacts, Opportunities).\n- **Flows**: Visual automation logic.\n- **Validation Rules**: Preventing bad data entry.",
        "framework": "1. **Security**: Profiles and Roles.\n2. **Automation**: Process Builder (Legacy) -> Flow.\n3. **Reporting**: Dashboards for leadership.",
        "standards": "- Avoid **Hardcoded IDs**."
    },
    {
        "filename": "business/actuary.md",
        "name": "Actuary",
        "description": "Expertise in risk probability, mortality tables, and financial modeling.",
        "domain": "business",
        "tags": ["math", "statistics", "insurance", "risk"],
        "role": "You put a price on uncertainty.",
        "concepts": "- **Law of Large Numbers**: Variance decreases as n increases.\n- **Present Value**: Money today > Money tomorrow.\n- **Risk Pooling**: Sharing losses across a group.",
        "framework": "1. **Data Collection**: Historical loss rates.\n2. **Modeling**: GLM (Generalized Linear Models).\n3. **Pricing**: Setting the premium.",
        "standards": "- Pass **Regulatory Scrutiny**."
    }
]

def create_skills():
    print(f"Generating {len(SKILLS)} skills (Batch 8)...")
    for skill in SKILLS:
        filepath = BASE_DIR / skill['filename']
        
        # Ensure dir exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        content = TEMPLATE.format(
            name=skill['name'],
            description=skill['description'],
            domain=skill['domain'],
            tags=str(skill['tags']),
            role=skill['role'],
            concepts=skill['concepts'],
            framework=skill['framework'],
            standards=skill['standards']
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created: {filepath}")

if __name__ == "__main__":
    create_skills()
