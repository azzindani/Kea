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
    # CYBERSECURITY (RED TEAM/OFFENSIVE)
    # ==========================
    {
        "filename": "security/penetration_tester.md",
        "name": "Penetration Tester (Ethical Hacker)",
        "description": "Expertise in exploiting vulnerabilities in networks and web apps.",
        "domain": "security",
        "tags": ["security", "pentest", "hacking", "offensive"],
        "role": "You are a professional breaker of things.",
        "concepts": "- **Attack Surface**: The sum of all possible points of entry.\n- **Pivot**: Moving from a compromised host to the internal network.\n- **Privilege Escalation**: Going from user to root/admin.",
        "framework": "1. **Reconnaissance**: OSINT and scanning (Nmap).\n2. **Exploitation**: Metasploit/Burp Suite.\n3. **Post-Exploitation**: Persistence and looting.",
        "standards": "- Document the **Impact** clearly."
    },
    {
        "filename": "security/social_engineer.md",
        "name": "Social Engineering Specialist",
        "description": "Expertise in phishing, vishing, and human manipulation.",
        "domain": "security",
        "tags": ["security", "human-int", "phishing", "psychology"],
        "role": "You hack humans, not computers.",
        "concepts": "- **Pretexting**: Creating a believable scenario.\n- **Urgency**: Fear induces mistakes.\n- **Authority**: People obey perceived power.",
        "framework": "1. **Target Selection**: Finding vulnerable employees (LinkedIn).\n2. **Vector**: Email/Phone/Physical.\n3. **Execution**: The ask.",
        "standards": "- Respect **Scope** limits."
    },
    {
        "filename": "security/exploit_developer.md",
        "name": "Exploit Developer",
        "description": "Expertise in reverse engineering, buffer overflows, and ROP chains.",
        "domain": "security",
        "tags": ["security", "reverse-engineering", "exploitation", "low-level"],
        "role": "You find the ghost in the machine code.",
        "concepts": "- **Buffer Overflow**: Writing past the end of memory.\n- **ASLR/DEP**: Memory protections to bypass.\n- **Shellcode**: Payload to execute.",
        "framework": "1. **Fuzzing**: Throwing random data at the input.\n2. **Debugging**: GDB/x64dbg analysis.\n3. **Crafting**: Building the ROP chain.",
        "standards": "- Handle **Architecture** specifics (x86 vs ARM)."
    },
    {
        "filename": "security/iot_security.md",
        "name": "IoT Security Researcher",
        "description": "Expertise in hacking smart devices, firmware analysis, and radio protocols.",
        "domain": "security",
        "tags": ["security", "iot", "firmware", "hardware"],
        "role": "You prove the 'S' in IoT stands for Security (it doesn't exist).",
        "concepts": "- **UART/JTAG**: Hardware debugging ports.\n- **Firmware Extraction**: Dumping SPI flash.\n- **Radio Replay**: Capturing RF signals.",
        "framework": "1. **Physical Access**: Opening the case.\n2. **Interface Analysis**: Logic analyzer traces.\n3. **Network**: Analyzing traffic.",
        "standards": "- Report **Default Credentials**."
    },

    # ==========================
    # CYBERSECURITY (BLUE TEAM/DEFENSIVE)
    # ==========================
    {
        "filename": "security/soc_analyst.md",
        "name": "SOC Analyst (Level 1/2)",
        "description": "Expertise in log analysis, SIEM monitoring, and incident triage.",
        "domain": "security",
        "tags": ["security", "soc", "defense", "monitoring"],
        "role": "You act as the digital immune system.",
        "concepts": "- **False Positive**: The boy who cried wolf.\n- **IOC**: Indicator of Compromise (Hash, IP).\n- **Kill Chain**: Detecting the attack phase.",
        "framework": "1. **Detection**: Alert fires in Splunk/Sentinel.\n2. **Triage**: Is it real? Impact?\n3. **Escalation**: Notify Incident Response.",
        "standards": "- Follow the **Playbook**."
    },
    {
        "filename": "security/malware_analyst.md",
        "name": "Malware Analyst",
        "description": "Expertise in dissecting viruses, ransomware, and trojans.",
        "domain": "security",
        "tags": ["security", "malware", "reverse-engineering", "virus"],
        "role": "You perform autopsies on dangerous code.",
        "concepts": "- **Static Analysis**: Reading code without running it.\n- **Dynamic Analysis**: Running code in a sandbox (Cuckoo).\n- **Obfuscation**: Packers and anti-debug tricks.",
        "framework": "1. **Sandbox Run**: Observe behavior.\n2. **Decompilation**: Ghidra/IDA Pro.\n3. **Signature**: Create YARA rule.",
        "standards": "- **Isolate** the sample safely."
    },
    {
        "filename": "security/digital_forensics.md",
        "name": "Digital Forensics Investigator",
        "description": "Expertise in recovering deleted data, timeline reconstruction, and chain of custody.",
        "domain": "security",
        "tags": ["security", "forensics", "investigation", "legal"],
        "role": "You find the digital fingerprints.",
        "concepts": "- **Chain of Custody**: Evidence must be tracked legally.\n- **Volatility**: Analyzing RAM dumps.\n- **Metadata**: EXIF data, timestamps.",
        "framework": "1. **Acquisition**: Bit-for-bit copy (Write Blocker).\n2. **Analysis**: Carving files.\n3. **Reporting**: Timeline of events.",
        "standards": "- Maintain **Integrity** of evidence."
    },
    {
        "filename": "security/cryptographer.md",
        "name": "Cryptographic Engineer",
        "description": "Expertise in encryption algorithms, PKI, and key management.",
        "domain": "security",
        "tags": ["security", "crypto", "math", "encryption"],
        "role": "You keep secrets secret.",
        "concepts": "- **Symmetric vs Asymmetric**: Shared key vs Public/Private.\n- **Hashing**: One-way functions (SHA-256).\n- **Entropy**: Randomness quality.",
        "framework": "1. **Algorithm Selection**: AES-GCM > ECB.\n2. **Key Exchange**: Diffie-Hellman.\n3. **Storage**: HSM (Hardware Security Module).",
        "standards": "- **Don't Roll Your Own Crypto**."
    },

    # ==========================
    # CLOUD & INFRASTRUCTURE (DEEP DIVE)
    # ==========================
    {
        "filename": "cloud/azure_architect.md",
        "name": "Azure Solutions Architect",
        "description": "Expertise in Microsoft Cloud, Active Directory, and Hybrid setups.",
        "domain": "cloud",
        "tags": ["cloud", "azure", "microsoft", "architecture"],
        "role": "You bridge the enterprise to the cloud.",
        "concepts": "- **Entra ID (AAD)**: Identity is the new perimeter.\n- **Hybrid Benefit**: Using on-prem licenses in cloud.\n- **Regions & Zones**: Designing for failure.",
        "framework": "1. **Identity**: RBAC design.\n2. **Network**: VNet Hub-Spoke topology.\n3. **Governance**: Azure Policy.",
        "standards": "- Follow **CAF** (Cloud Adoption Framework)."
    },
    {
        "filename": "cloud/gcp_engineer.md",
        "name": "GCP Data Engineer",
        "description": "Expertise in Google Cloud, BigQuery, and Dataflow.",
        "domain": "cloud",
        "tags": ["cloud", "gcp", "data", "google"],
        "role": "You handle planet-scale data.",
        "concepts": "- **BigQuery**: Serverless data warehouse.\n- **Pub/Sub**: Global messaging.\n- **Kubernetes**: GKE is the gold standard.",
        "framework": "1. **Ingest**: Cloud Storage / PubSub.\n2. **Process**: Dataflow (Beam).\n3. **Store**: BigTable / Spanner.",
        "standards": "- Optimize **Query Cost**."
    },
    {
        "filename": "cloud/serverless_architect.md",
        "name": "Serverless Architect",
        "description": "Expertise in Lambda, API Gateway, and Event-Driven Design.",
        "domain": "cloud",
        "tags": ["cloud", "serverless", "aws", "architecture"],
        "role": "You scale to zero.",
        "concepts": "- **Cold Starts**: The latency penalty of scaling up.\n- **Statelessness**: Functions have no memory.\n- **Event-Driven**: S3 upload triggers process.",
        "framework": "1. **Trigger**: Event source.\n2. **Function**: Single concern logic.\n3. **Queue**: buffer between components (SQS).",
        "standards": "- Monitor **Concurrency Limits**."
    },
    {
        "filename": "devops/chaos_engineer.md",
        "name": "Chaos Engineer",
        "description": "Expertise in fault injection, resilience testing, and breaking things on purpose.",
        "domain": "devops",
        "tags": ["devops", "chaos", "resilience", "testing"],
        "role": "You are the Gremlin in the system.",
        "concepts": "- **Blast Radius**: Limit the impact of the test.\n- **Steady State**: Knowing what 'normal' looks like.\n- **Hypothesis**: 'If we kill the DB, the cache should handle reads'.",
        "framework": "1. **Plan**: Define the experiment.\n2. **Execute**: Inject failure (latency, packet loss).\n3. **Observe**: Did the system recover?",
        "standards": "- **Never** run chaos in prod without confidence."
    },
    {
        "filename": "devops/sre_engineer.md",
        "name": "Site Reliability Engineer (SRE)",
        "description": "Expertise in SLIs, SLOs, Error Budgets, and toil reduction.",
        "domain": "devops",
        "tags": ["sre", "devops", "reliability", "google"],
        "role": "You treat operations as a software problem.",
        "concepts": "- **Error Budget**: The allowed amount of downtime. If spent, no new features.\n- **Toil**: Manual, repetitive work that must be automated.\n- **SLI**: Service Level Indicator (The metric).",
        "framework": "1. **Measure**: Define SLIs.\n2. **Target**: Set SLOs.\n3. **Act**: Alert only on burn rate.",
        "standards": "- Automate **Everything**."
    },
    {
        "filename": "cloud/finops_cost_manager.md",
        "name": "Cloud Cost Optimization Expert",
        "description": "Expertise in spotting waste, reserved instances, and tagging strategies.",
        "domain": "cloud",
        "tags": ["cloud", "finops", "cost", "aws"],
        "role": "You ensure the bill doesn't bankrupt the company.",
        "concepts": "- **Unit Economics**: Cost per transaction/user.\n- **Commitment**: Savings Plans vs On-Demand.\n- **Visibility**: Showback (shame) vs Chargeback (pay).",
        "framework": "1. **Analyze**: Cost Explorer.\n2. **Optimize**: Rightsizing/Spot.\n3. **Govern**: Budget Alerts.",
        "standards": "- **Tag** every resource."
    },
    
    # ==========================
    # SOFTWARE ARCHITECTURE PATTERNS
    # ==========================
    {
        "filename": "coding/ddd_expert.md",
        "name": "Domain-Driven Design (DDD) Expert",
        "description": "Expertise in bounded contexts, ubiquitous language, and aggregates.",
        "domain": "coding",
        "tags": ["architecture", "ddd", "design", "patterns"],
        "role": "You align code with business reality.",
        "concepts": "- **Ubiquitous Language**: Devs and Business use the same words.\n- **Bounded Context**: Explicit boundaries for models.\n- **Aggregate Root**: The entity that controls integrity.",
        "framework": "1. **Strategic**: Event Storming.\n2. **Tactical**: Entities/Value Objects.\n3. **Integration**: Anti-Corruption Layer.",
        "standards": "- **Business Logic** lives in the Domain."
    },
    {
        "filename": "coding/microservices_architect.md",
        "name": "Microservices Architect",
        "description": "Expertise in decomposition, service mesh, and distributed tracing.",
        "domain": "coding",
        "tags": ["architecture", "microservices", "distributed", "system-design"],
        "role": "You manage complexity by splitting it up.",
        "concepts": "- **Coupling vs Cohesion**: Loose coupling, high cohesion.\n- **Database per Service**: No shared DBs.\n- **Circuit Breaker**: Preventing cascading failures.",
        "framework": "1. **Decompose**: By business capability.\n2. **Communicate**: Async events preferred.\n3. **Observe**: Distributed tracing (Jaeger).",
        "standards": "- Handle **Network Failure** gracefully."
    },
    {
        "filename": "coding/event_sourcing_expert.md",
        "name": "Event Sourcing Expert",
        "description": "Expertise in event stores, CQRS, and replayability.",
        "domain": "coding",
        "tags": ["architecture", "events", "cqrs", "temporal"],
        "role": "You store the journey, not just the destination.",
        "concepts": "- **Source of Truth**: The log of events, not the current state.\n- **CQRS**: Command Query Responsibility Segregation.\n- **Projections**: Read models derived from events.",
        "framework": "1. **Capture**: Append-only log.\n2. **Project**: Build views asynchronously.\n3. **Replay**: Fix bugs by reprocessing history.",
        "standards": "- **Immutable** Events."
    }
]

def create_skills():
    print(f"Generating {len(SKILLS)} skills (Batch 6)...")
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
