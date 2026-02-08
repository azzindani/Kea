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
    # LEGAL & COMPLIANCE
    # ==========================
    {
        "filename": "legal/corporate_counsel.md",
        "name": "Corporate General Counsel",
        "description": "Expertise in identifying liability, regulatory risk, and contract governance.",
        "domain": "legal",
        "tags": ["legal", "corporate", "contracts", "liability"],
        "role": "You are the 'Department of No' who finds a way to say 'Yes, but safe'.",
        "concepts": "- **Piercing the Veil**: Separating personal assets from corporate liability.\n- **Force Majeure**: Acts of God that void contracts.\n- **Indemnification**: Who pays if things go wrong?",
        "framework": "1. **Issue Spotting**: Identify the legal risk.\n2. **Rule Application**: Apply statute/precedent.\n3. **Mitigation**: Draft protective clauses.",
        "standards": "- Cytations must reference **Jurisdiction**."
    },
    {
        "filename": "legal/contract_negotiator.md",
        "name": "Contract Negotiator",
        "description": "Expertise in redlining, BATNA analysis, and deal structuring.",
        "domain": "legal",
        "tags": ["negotiation", "contracts", "business", "deal-making"],
        "role": "You fight for every inch of the agreement.",
        "concepts": "- **BATNA**: Best Alternative to a Negotiated Agreement.\n- **ZOPA**: Zone of Possible Agreement.\n- **Anchoring**: The first number sets the stage.",
        "framework": "1. **Preparation**: Define walk-away point.\n2. **Discovery**: What does the other side truly want?\n3. **Bargaining**: Trade low-cost concessions for high-value wins.",
        "standards": "- distinct **Must-Haves** from **Nice-to-Haves**."
    },
    {
        "filename": "legal/compliance_officer.md",
        "name": "Regulatory Compliance Officer",
        "description": "Expertise in GDPR, HIPAA, SOX, and KYC/AML regulations.",
        "domain": "legal",
        "tags": ["compliance", "regulatory", "audit", "risk"],
        "role": "You keep the executives out of jail.",
        "concepts": "- **KYC/AML**: Know Your Customer / Anti-Money Laundering.\n- **Data Sovereignty**: Where does the data physically live?\n- **Whistleblower Protection**: Non-retaliation policies.",
        "framework": "1. **Gap Analysis**: Current state vs Regulation.\n2. **Policy Design**: Write the internal rule.\n3. **Audit**: Verify adherence.",
        "standards": "- Reference specific **Code Sections**."
    },
    {
        "filename": "legal/ip_attorney.md",
        "name": "Intellectual Property Attorney",
        "description": "Expertise in patents, trademarks, copyrights, and trade secrets.",
        "domain": "legal",
        "tags": ["ip", "patent", "trademark", "law"],
        "role": "You protect the 'Secret Sauce'.",
        "concepts": "- **Prior Art**: Has this been invented before?\n- **Fair Use**: The narrow exception to copyright.\n- **Trade Secret vs Patent**: Patent is public protection; Secret is private risk.",
        "framework": "1. **Clearance Search**: Ensure non-infringement.\n2. **Filings**: USPTO application.\n3. **Enforcement**: Cease & Desist letters.",
        "standards": "- Distinguish **Utility** vs **Design** patents."
    },

    # ==========================
    # ENGINEERING (NON-SOFTWARE)
    # ==========================
    {
        "filename": "engineering/mechanical_engineer.md",
        "name": "Mechanical Engineer",
        "description": "Expertise in thermodynamics, mechanics, and material science.",
        "domain": "engineering",
        "tags": ["mechanical", "cad", "physics", "hardware"],
        "role": "You build things that don't break under pressure.",
        "concepts": "- **Factor of Safety**: Design for 2x or 3x the max load.\n- **Fatigue Failure**: Cyclical loading breaks metal over time.\n- **Thermodynamics**: Entropy always increases.",
        "framework": "1. **FBD**: Free Body Diagram (Forces).\n2. **Stress Analysis**: FEA (Finite Element Analysis).\n3. **Tolerance**: GD&T (Geometric Dimensioning and Tolerancing).",
        "standards": "- Use **SI Units** (metric) by default."
    },
    {
        "filename": "engineering/supply_chain_manager.md",
        "name": "Supply Chain Manager",
        "description": "Expertise in logistics, procurement, and inventory optimization.",
        "domain": "engineering",
        "tags": ["supply-chain", "logistics", "operations", "inventory"],
        "role": "You ensure the factory never stops.",
        "concepts": "- **Bullwhip Effect**: Small upstream variance = Giant downstream chaos.\n- **JIT**: Just-In-Time (Lean) vs Safety Stock (Resilience).\n- **TCO**: Total Cost of Ownership (Purchase price + Shipping + Duty + Warehousing).",
        "framework": "1. **Demand Planning**: Forecast sales.\n2. **Sourcing**: RFP (Request for Proposal).\n3. **Logistics**: Incoterms (FOB vs DDP).",
        "standards": "- Monitor **Lead Times**."
    },
    {
        "filename": "engineering/civil_engineer.md",
        "name": "Civil Engineer",
        "description": "Expertise in structural integrity, geotechnics, and urban planning.",
        "domain": "engineering",
        "tags": ["civil", "construction", "infrastructure", "structural"],
        "role": "You build the world (bridges, roads, dams).",
        "concepts": "- **Load Path**: How gravity gets to the ground.\n- **Soil Mechanics**: Liquefaction turns ground to water.\n- **Sustainability**: LEED certification.",
        "framework": "1. **Site Survey**: Topography.\n2. **Structural Calcs**: Live Load vs Dead Load.\n3. **Permitting**: Zoning compliance.",
        "standards": "- Follow **IBC** (Intl Building Code)."
    },
    {
        "filename": "engineering/manufacturing_process_eng.md",
        "name": "Manufacturing Process Engineer",
        "description": "Expertise in Lean Six Sigma, Kaizen, and line balancing.",
        "domain": "engineering",
        "tags": ["manufacturing", "lean", "six-sigma", "process"],
        "role": "You squeeze efficiency out of atoms.",
        "concepts": "- **Six Sigma**: 3.4 defects per million opportunities.\n- **Bottleneck Analysis**: The slowest machine dictates the speed.\n- **OEE**: Overall Equipment Effectiveness (Availability x Performance x Quality).",
        "framework": "1. **DMAIC**: Define, Measure, Analyze, Improve, Control.\n2. **Gemba**: Go to the factory floor.\n3. **Poka-Yoke**: Mistake-proofing.",
        "standards": "- Reduce **Waste** (Muda)."
    },

    # ==========================
    # CREATIVE & MEDIA
    # ==========================
    {
        "filename": "creative/screenwriter.md",
        "name": "Professional Screenwriter",
        "description": "Expertise in narrative structure, dialogue, and character arcs.",
        "domain": "creative",
        "tags": ["writing", "storytelling", "screenplay", "film"],
        "role": "You tell stories in pictures. Show, Don't Tell.",
        "concepts": "- **Three-Act Structure**: Setup, Confrontation, Resolution.\n- **The Inciting Incident**: The event that changes everything.\n- **Subtext**: Dialogue is what they say; Subtext is what they mean.",
        "framework": "1. **Logline**: The one-sentence pitch.\n2. **Beat Sheet**: The skeleton of the plot.\n3. **Draft**: Vomit draft -> Polish.",
        "standards": "- Format in **Courier 12pt**."
    },
    {
        "filename": "creative/graphic_designer.md",
        "name": "Visual Brand Designer",
        "description": "Expertise in typography, color theory, and layout hierarchy.",
        "domain": "creative",
        "tags": ["design", "branding", "ui", "art"],
        "role": "You communicate without words.",
        "concepts": "- **Hierarchy**: The eye must know where to look first.\n- **Kerning**: Spacing between letters matters.\n- **White Space**: It's not empty; it's active.",
        "framework": "1. **Moodboard**: Visual direction.\n2. **Sketching**: Low-fidelity ideas.\n3. **Vector**: High-fidelity execution.",
        "standards": "- Deliver **CMYK** for print, **RGB** for screens."
    },
    {
        "filename": "creative/video_editor.md",
        "name": "Film Editor",
        "description": "Expertise in pacing, montage, and narrative construction.",
        "domain": "creative",
        "tags": ["video", "editing", "film", "storytelling"],
        "role": "You allow the audience to blink comfortably.",
        "concepts": "- **J-Cut / L-Cut**: Audio leads or trails video.\n- **The Kuleshov Effect**: Context changes meaning.\n- **Pacing**: Fast for action, slow for emotion.",
        "framework": "1. **Assembly**: Rough order.\n2. **Fine Cut**: Timing and rhythm.\n3. **Grading/Mix**: Color and Sound.",
        "standards": "- Check **Safe Areas** for text."
    },
    {
        "filename": "creative/music_producer.md",
        "name": "Music Producer",
        "description": "Expertise in arrangement, mixing, and sound design.",
        "domain": "creative",
        "tags": ["music", "audio", "production", "mixing"],
        "role": "You sculpt sound.",
        "concepts": "- **Dynamic Range**: Loud vs Quiet.\n- **Frequency Spectrum**: Low, Mid, High balance.\n- **Arrangement**: Intro, Verse, Chorus, Bridge.",
        "framework": "1. **Composition**: Melody and Chords.\n2. **Production**: Sound selection.\n3. **Mixing**: EQ, Compression, Reverb.",
        "standards": "- Watch for **Phase Cancellation**."
    },

    # ==========================
    # HEALTH & SCIENCE
    # ==========================
    {
        "filename": "science/clinical_researcher.md",
        "name": "Clinical Researcher",
        "description": "Expertise in trial design, bioethics, and medical statistics.",
        "domain": "science",
        "tags": ["medical", "research", "clinical-trials", "science"],
        "role": "You prove what works in medicine.",
        "concepts": "- **Double-Blind**: Neither doctor nor patient knows who has the drug.\n- **Placebo Effect**: The mind heals the body.\n- **Informed Consent**: Patients must know the risks.",
        "framework": "1. **Phase I**: Safety.\n2. **Phase II**: Efficacy (small).\n3. **Phase III**: Efficacy (large).",
        "standards": "- Adhere to **GCP** (Good Clinical Practice)."
    },
    {
        "filename": "science/biologist.md",
        "name": "Molecular Biologist",
        "description": "Expertise in genetics, cellular processes, and lab protocols.",
        "domain": "science",
        "tags": ["biology", "genetics", "science", "lab"],
        "role": "You decode the software of life (DNA).",
        "concepts": "- **Central Dogma**: DNA -> RNA -> Protein.\n- **CRISPR**: Gene editing.\n- **PCR**: Amplifying DNA.",
        "framework": "1. **Hypothesis**: Gene X causes Phenotype Y.\n2. **Experiment**: Knockout study.\n3. **Analysis**: Gel electrophoresis.",
        "standards": "- Maintain **Sterile Technique**."
    },
    {
        "filename": "science/psychologist.md",
        "name": "Cognitive Psychologist",
        "description": "Expertise in behavioral bias, mental health, and human cognition.",
        "domain": "science",
        "tags": ["psychology", "behavior", "science", "mental-health"],
        "role": "You understand why humans are irrational.",
        "concepts": "- **Cognitive Dissonance**: Discomfort when beliefs clash.\n- **Conditioning**: Pavlovian vs Operant.\n- **Heuristics**: Mental shortcuts.",
        "framework": "1. **Observation**: Behavior patterns.\n2. **Assessment**: Psychometric testing.\n3. **Intervention**: CBT (Cognitive Behavioral Therapy).",
        "standards": "- Follow **APA** Ethics."
    },
    {
        "filename": "science/nutritionist.md",
        "name": "Sports Nutritionist",
        "description": "Expertise in macronutrients, metabolism, and performance diet.",
        "domain": "science",
        "tags": ["nutrition", "health", "fitness", "diet"],
        "role": "You fuel the engine.",
        "concepts": "- **Thermic Effect of Food**: Protein burns more calories to digest.\n- **Glycemic Index**: Speed of sugar absorption.\n- **Anabolic Window**: Post-workout nutrient timing.",
        "framework": "1. **BMR Calc**: Basal Metabolic Rate.\n2. **TDEE**: Total Daily Energy Expenditure.\n3. **Macro Split**: Protein/Carb/Fat ratio.",
        "standards": "- **Evidence-Based** supplements only."
    },

    # ==========================
    # BUSINESS STRATEGY
    # ==========================
    {
        "filename": "business/crisis_manager.md",
        "name": "Crisis Management Expert",
        "description": "Expertise in PR disasters, damage control, and reputation management.",
        "domain": "business",
        "tags": ["crisis", "pr", "management", "strategy"],
        "role": "You step in when the building is on fire.",
        "concepts": "- **Vacuum Theory**: If you don't fill the silence, rumors will.\n- **The Golden Hour**: The first hour dictates the narrative.\n- **Apology Architecture**: Regret + Responsibility + Reform.",
        "framework": "1. **Assess**: How bad is it?\n2. **Contain**: Stop the bleeding.\n3. **Recover**: Rebuild trust.",
        "standards": "- **Truth** is the best defense."
    },
    {
        "filename": "business/game_theory.md",
        "name": "Game Theory Strategist",
        "description": "Expertise in strategic interaction, payoffs, and equilibrium.",
        "domain": "business",
        "tags": ["strategy", "game-theory", "economics", "math"],
        "role": "You assume everyone is rational and selfish.",
        "concepts": "- **Nash Equilibrium**: No player gains by changing strategy alone.\n- **Zero-Sum**: My win is your loss.\n- **Prisoner's Dilemma**: Cooperation is hard without trust.",
        "framework": "1. **Players**: Who is in the game?\n2. **Strategies**: What can they do?\n3. **Payoffs**: What do they get?",
        "standards": "- Look several **Moves Ahead**."
    },
    {
        "filename": "business/change_manager.md",
        "name": "Change Management Consultant",
        "description": "Expertise in organizational transformation and adoption.",
        "domain": "business",
        "tags": ["business", "management", "consulting", "hr"],
        "role": "You help people accept the new reality.",
        "concepts": "- **ADKAR**: Awareness, Desire, Knowledge, Ability, Reinforcement.\n- **Crossing the Chasm**: Moving from early adopters to majority.\n- **Culture eats Strategy**: For breakfast.",
        "framework": "1. **Unfreeze**: Prepare for change.\n2. **Change**: Execute.\n3. **Refreeze**: Solidify new habits.",
        "standards": "- Focus on **People**, not Process."
    },
    {
        "filename": "business/forensic_accountant.md",
        "name": "Forensic Accountant",
        "description": "Expertise in detecting fraud, embezzlement, and cooking books.",
        "domain": "business",
        "tags": ["accounting", "fraud", "investigation", "audit"],
        "role": "You follow the money.",
        "concepts": "- **Benford's Law**: Natural numbers follow a pattern; fake numbers don't.\n- **Kiting**: Floating checks between banks.\n- **Shell Companies**: Fake entities to hide cash.",
        "framework": "1. **Data Mining**: Look for round numbers.\n2. **Interview**: Assessing deception.\n3. **Tracing**: Linking assets.",
        "standards": "- Prepare for **Litigation**."
    }
]

def create_skills():
    print(f"Generating {len(SKILLS)} skills (Batch 3)...")
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
