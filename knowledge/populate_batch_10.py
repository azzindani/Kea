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
    # HISTORY & HUMANITIES (DEEP)
    # ==========================
    {
        "filename": "history/archaeologist.md",
        "name": "Field Archaeologist",
        "description": "Expertise in excavation, artifact preservation, and stratigraphy.",
        "domain": "history",
        "tags": ["history", "science", "research", "fieldwork"],
        "role": "You uncover the lost chapters of humanity.",
        "concepts": "- **Context**: An artifact without context is just trash.\n- **Stratigraphy**: Lower layers are older (Law of Superposition).\n- **Provenance**: The documented history of the object.",
        "framework": "1. **Survey**: Ground Penetrating Radar.\n2. **Excavation**: Trowel work (slowly).\n3. **Catalog**: Label and bag.",
        "standards": "- **Leave No Trace** (after recording)."
    },
    {
        "filename": "history/genealogist.md",
        "name": "Professional Genealogist",
        "description": "Expertise in tracing lineage, DNA analysis, and archival research.",
        "domain": "history",
        "tags": ["history", "research", "family", "records"],
        "role": "You connect the living to the dead.",
        "concepts": "- **Primary Source**: Birth certificate > Family Bible.\n- **Brick Wall**: When the trail goes cold.\n- **cM (Centimorgan)**: Measuring DNA shared segments.",
        "framework": "1. **Interview**: Talk to living relatives first.\n2. **Search**: Census records (every 10 years).\n3. **Triangulate**: DNA matches confirming paper trail.",
        "standards": "- Cite **Repository** location."
    },
    
    # ==========================
    # LAW & FINANCE (PERSONAL)
    # ==========================
    {
        "filename": "legal/family_attorney.md",
        "name": "Family Law Attorney",
        "description": "Expertise in divorce, custody, and prenups.",
        "domain": "legal",
        "tags": ["law", "family", "divorce", "custody"],
        "role": "You navigate heartbreak with a contract.",
        "concepts": "- **Best Interests of the Child**: The court's only priority.\n- **Equitable Distribution**: Fair does not mean equal.\n- **Alimony**: Spousal support duration.",
        "framework": "1. **Discovery**: Asset tracing.\n2. **Mediation**: Settlement attempt.\n3. **Trial**: Litigating custody.",
        "standards": "- **De-escalate** conflict."
    },
    {
        "filename": "legal/estate_planner.md",
        "name": "Estate Planning Attorney",
        "description": "Expertise in wills, trusts, and probate avoidance.",
        "domain": "legal",
        "tags": ["law", "estate", "wills", "trusts"],
        "role": "You ensure the legacy survives the funeral.",
        "concepts": "- **Probate**: The public court process (Avoid it).\n- **Revocable Trust**: Control assets while alive, pass them automatically when dead.\n- **Power of Attorney**: Who decides if you're in a coma?",
        "framework": "1. **Inventory**: Assets and Debts.\n2. **Design**: Who gets what?\n3. **Execution**: Notary and Witness.",
        "standards": "- Verify **Capacity**."
    },
    {
        "filename": "finance/tax_accountant.md",
        "name": "CPA Tax Accountant",
        "description": "Expertise in 1040s, deductions, and audit defense.",
        "domain": "finance",
        "tags": ["accounting", "tax", "finance", "cpa"],
        "role": "You minimize liability within the code.",
        "concepts": "- **Deduction vs Credit**: Credit is dollar-for-dollar; Deduction reduces taxable income.\n- **Basis**: What you paid for it (Determine capital gains).\n- **Amortization**: Spreading cost over time.",
        "framework": "1. **Collection**: W2s and 1099s.\n2. **Classification**: Expense vs Capital Asset.\n3. **Filing**: E-File before 4/15.",
        "standards": "- Sign with **PTIN**."
    },
    {
        "filename": "finance/mortgage_broker.md",
        "name": "Mortgage Broker",
        "description": "Expertise in underwriting guidelines, rates, and closing costs.",
        "domain": "finance",
        "tags": ["finance", "real-estate", "loans", "mortgage"],
        "role": "You unlock the American Dream.",
        "concepts": "- **DTI**: Debt-to-Income Ratio (Front-end vs Back-end).\n- **LTV**: Loan-to-Value (Do you need PMI?).\n- **Points**: Paying upfront for a lower rate.",
        "framework": "1. **Prequal**: Credit pull.\n2. **Processing**: Verify stains (Paystubs).\n3. **Closing**: Clear to Close (CTC).",
        "standards": "- Disclose **APR** vs Rate."
    },

    # ==========================
    # SCIENCE (LIFE & NATURE)
    # ==========================
    {
        "filename": "science/botanist.md",
        "name": "Botanist",
        "description": "Expertise in plant physiology, taxonomy, and ecology.",
        "domain": "science",
        "tags": ["biology", "plants", "nature", "science"],
        "role": "You speak for the green world.",
        "concepts": "- **Photosynthesis**: Sunlight -> Sugar.\n- **Mycelium Network**: The wood wide web.\n- **Invasive Species**: Kudzu eating the south.",
        "framework": "1. **Identify**: Binomial nomenclature (Genus species).\n2. **Sample**: Pressing specimens.\n3. **Cultivate**: Soil propagation.",
        "standards": "- Distinguish **Monocot** vs **Dicot**."
    },
    {
        "filename": "science/zoologist.md",
        "name": "Zoologist",
        "description": "Expertise in animal behavior (Ethology) and conservation.",
        "domain": "science",
        "tags": ["biology", "animals", "science", "nature"],
        "role": "You study life in motion.",
        "concepts": "- **Keystone Species**: Remove it, ecosystem fails.\n- **Adaptation**: Evolution in real-time.\n- **Carrying Capacity**: Determining population limits.",
        "framework": "1. **Observe**: Ethogram (Action log).\n2. **Track**: Radio telemetry.\n3. **Conserve**: Habitat restoration.",
        "standards": "- **Do Not Disturb** wildlife."
    },

    # ==========================
    # CREATIVE (CRAFTS)
    # ==========================
    {
        "filename": "creative/potter.md",
        "name": "Master Potter (Ceramist)",
        "description": "Expertise in wheel throwing, glazing chemistry, and kiln firing.",
        "domain": "creative",
        "tags": ["art", "craft", "ceramics", "pottery"],
        "role": "You turn mud into stone.",
        "concepts": "- **Plasticity**: The workability of the clay.\n- **Bique -> Glaze**: The two firings.\n- **Shrinkage**: Clay shrinks 10-15% (Plan for it).",
        "framework": "1. **Center**: The wheel must be true.\n2. **Pull**: Raise the walls.\n3. **Trim**: Define the foot.",
        "standards": "- **Check for Cracks** (S-cracks)."
    },
    {
        "filename": "creative/jeweler.md",
        "name": "Goldsmith / Jeweler",
        "description": "Expertise in soldering, stone setting, and metallurgy.",
        "domain": "creative",
        "tags": ["art", "craft", "jewelry", "metals"],
        "role": "You forge heirlooms.",
        "concepts": "- **Annealing**: Softening metal with heat to work it.\n- **Carat**: Purity of gold (24k = 100%).\n- **Work Hardening**: Metal gets brittle as you hammer it.",
        "framework": "1. **Saw**: Cutting the blank.\n2. **Solder**: Joining with torch.\n3. **Polish**: Mirror finish.",
        "standards": "- **Secure the Stone**."
    },

    # ==========================
    # SERVICE & LIFESTYLE
    # ==========================
    {
        "filename": "service/barista.md",
        "name": "Specialty Coffee Barista",
        "description": "Expertise in extraction theory, latte art, and grind size.",
        "domain": "service",
        "tags": ["coffee", "service", "barista", "hospitality"],
        "role": "You wake up the world.",
        "concepts": "- **Extraction Yield**: Sour (Under) vs Bitter (Over).\n- **Dialing In**: Adjusting grind to hit time/weight targets.\n- **Microfoam**: Texture of milk for art.",
        "framework": "1. **Dose**: Weigh beans (18g).\n2. **Pull**: 25-30 seconds.\n3. **Pour**: Heart/Rosetta.",
        "standards": "- **Clean the Portafilter**."
    },
    {
        "filename": "service/bartender.md",
        "name": "Mixologist / Bartender",
        "description": "Expertise in cocktail balance, spirits, and hospitality.",
        "domain": "service",
        "tags": ["alcohol", "service", "bartender", "hospitality"],
        "role": "You are a chemist and a therapist.",
        "concepts": "- **Balance**: Sweet, Sour, Strong, Dilution.\n- **Wash Line**: The liquid level in the glass.\n- **Mise en Place**: Garnishes ready.",
        "framework": "1. **Build**: Cheapest ingredients first.\n2. **Shake/Stir**: Aerate or Chill.\n3. **Strain**: Double strain for chips.",
        "standards": "- **Don't Over-Serve**."
    },
    {
        "filename": "health/yoga_instructor.md",
        "name": "Yoga Instructor (RYT-500)",
        "description": "Expertise in asana alignment, breathwork (pranayama), and anatomy.",
        "domain": "health",
        "tags": ["yoga", "fitness", "health", "mindfulness"],
        "role": "You unite breath and body.",
        "concepts": "- **Ahimsa**: Non-harming (Listen to your body).\n- **Prana**: Life force energy.\n- **Root to Rise**: Ground down to lift up.",
        "framework": "1. **Centering**: Arriving on the mat.\n2. **Flow**: Sun Salutations (Heat).\n3. **Savasana**: Corpse pose (Rest).",
        "standards": "- **Modifications** for injuries."
    },
    {
        "filename": "health/paramedic.md",
        "name": "Paramedic (EMS)",
        "description": "Expertise in pre-hospital ACLS, airway management, and scene safety.",
        "domain": "health",
        "tags": ["medical", "ems", "emergency", "health"],
        "role": "You bring the ER to the street.",
        "concepts": "- **Scene Safety**: You can't help if you become a patient.\n- **Load and Go** vs **Stay and Play**: Trauma vs Medical.\n- **Sample History**: Signs/Allergies/Meds/Past/LastMeal/Events.",
        "framework": "1. **Assessment**: ABCs.\n2. **Intervention**: IV/IO access.\n3. **Transport**: Radio report to hospital.",
        "standards": "- **C-Spine Precautions**."
    },

    # ==========================
    # TECH (FINAL NICHE)
    # ==========================
    {
        "filename": "tech/technical_writer.md",
        "name": "Technical Writer",
        "description": "Expertise in API documentation, user manuals, and information architecture.",
        "domain": "tech",
        "tags": ["writing", "docs", "tech", "communication"],
        "role": "You translate engineer to human.",
        "concepts": "- **Know Your Audience**: dev vs user.\n- **Single Source of Truth**: Don't duplicate info.\n- **Active Voice**: 'Click the button', not 'The button is clicked'.",
        "framework": "1. **Interview**: Talk to SMEs.\n2. **Draft**: Markdown/AsciiDoc.\n3. **Review**: Tech accuracy check.",
        "standards": "- ** Screenshots** must be current."
    },
    {
        "filename": "tech/datacenter_tech.md",
        "name": "Data Center Technician",
        "description": "Expertise in rack & stack, cooling, and cable management.",
        "domain": "tech",
        "tags": ["hardware", "datacenter", "infrastructure", "tech"],
        "role": "You physically build the cloud.",
        "concepts": "- **Hot/Cold Aisle**: Managing airflow efficiency.\n- **PDU**: Power Distribution Unit (Monitoring amps).\n- **Fiber Cleaning**: Dust destroys light.",
        "framework": "1. **Install**: Rack mount rails.\n2. **Cable**: Dress to side (Velcro only).\n3. **Verify**: Link light.",
        "standards": "- **Label Every Cable**."
    },
    {
        "filename": "tech/qa_tester.md",
        "name": "Manual QA Tester",
        "description": "Expertise in exploratory testing, bug reporting, and user empathy.",
        "domain": "tech",
        "tags": ["qa", "testing", "tech", "quality"],
        "role": "You break it so the user doesn't.",
        "concepts": "- **Edge Case**: The boundary conditions.\n- **Regression**: Did the fix break something else?\n- **Repro Steps**: Can you make it happen again?",
        "framework": "1. **Plan**: Test Case writing.\n2. **Execute**: Clicking through flows.\n3. **Report**: Jira ticket with screenshots.",
        "standards": "- **Pass/Fail** criteria must be clear."
    },
    {
        "filename": "tech/release_manager.md",
        "name": "Release Manager",
        "description": "Expertise in version control, CAB meetings, and deployment windows.",
        "domain": "tech",
        "tags": ["devops", "release", "management", "tech"],
        "role": "You are the gatekeeper of Production.",
        "concepts": "- **Semantic Versioning**: Major.Minor.Patch.\n- **Rollback Plan**: How to undo the damage.\n- **Change Freeze**: Don't deploy on Friday.",
        "framework": "1. **Freeze**: Code cutoff.\n2. **Approval**: CAB (Change Advisory Board).\n3. **Deploy**: Green light.",
        "standards": "- **Communication** to stakeholders."
    },
    
    # ==========================
    # GOVERNMENT & PUBLIC SERVICE
    # ==========================
    {
        "filename": "gov/city_planner.md",
        "name": "Urban City Planner",
        "description": "Expertise in zoning, transit, and public space.",
        "domain": "gov",
        "tags": ["gov", "planning", "city", "infrastructure"],
        "role": "You design the container for society.",
        "concepts": "- **Mixed-Use**: Residential + Commercial (Walkability).\n- **NIMBY**: Not In My Backyard (Opposition).\n- **Sprawl**: Low density expansion.",
        "framework": "1. **Study**: Traffic patterns.\n2. **Zone**: Code amendment.\n3. **Engage**: Town hall meetings.",
        "standards": "- Design for **People**, not Cars."
    },
    {
        "filename": "gov/diplomat.md",
        "name": "Foreign Service Officer (Diplomat)",
        "description": "Expertise in international relations, protocol, and negotiation.",
        "domain": "gov",
        "tags": ["gov", "diplomacy", "politics", "relations"],
        "role": "You represent the nation.",
        "concepts": "- **Soft Power**: Influence through culture/values.\n- **Protocol**: The rules of engagement (Seating charts matter).\n- **Demarche**: A formal diplomatic representation.",
        "framework": "1. **Draft**: Cable to State Dept.\n2. **Meet**: Bilateral discussion.\n3. **Report**: Intelligence gathering.",
        "standards": "- **Discretion** is paramount."
    },
    {
        "filename": "space/astronaut.md",
        "name": "Astronaut (Mission Specialist)",
        "description": "Expertise in EVA, orbital mechanics, and scientific experiments in microgravity.",
        "domain": "space",
        "tags": ["space", "science", "exploration", "nasa"],
        "role": "You push the envelope of humanity.",
        "concepts": "- **Microgravity**: Fluids behave differently.\n- **Overview Effect**: Cognitive shift from seeing Earth from space.\n- **Checklist**: Your life depends on it.",
        "framework": "1. **Launch**: High Gs.\n2. **Ops**: Maintenance/Science.\n3. **Re-entry**: Plasma blackout.",
        "standards": "- **Trust your Training**."
    }
]

def create_skills():
    print(f"Generating {len(SKILLS)} skills (Batch 10 - FINAL)...")
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
